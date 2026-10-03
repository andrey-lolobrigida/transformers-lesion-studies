"""E3 sweep driver on the tiny model: enumeration, cell specs, cell-set
records, resume, and CLI refusals. CPU, offline."""

import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.lesion import e3_sweep as S
from src.lesion.e3_prereg import ITEM, MAP, N_DIRECT, N_TOTAL, COMPONENTS, label
from src.lesion.runner import run
from src.lesion.spec import MLP, All, Head, Labels, Logits, MeanReference

COMPS = (Head(0, 0), Head(1, 1), MLP(0))  # valid on the 2-layer, 2-head tiny model
CONTEXT = {"gate_file": "none", "gap": 1.0, "gap_sem": 0.1, "fraction_removed": 1.0}


def run_tiny(model, battery, root, map_id="total_zero_unfrozen", ref_seed=None, keep=True, rev="r1", n=16,
             comps=COMPS):
    cs = S.CellSet("tiny", map_id, 0, ref_seed)
    return S.run_cell_set(model, battery, cs, comps, root / "sweep" / "tiny", root / "sweep" / "tiny" / "clean_s0.parquet",
                          n=n, prepend_bos=False, batch_size=8, keep_prompts=keep, rev=rev, command="test",
                          context=CONTEXT)


def test_enumeration_counts():
    items = tuple(ITEM)
    sel, floor = S.cell_sets(items, "selection"), S.cell_sets(items, "floor")
    assert len(sel) == 27 and len(sel) * len(COMPONENTS) == N_TOTAL + N_DIRECT == 4212
    assert len(floor) == 36 and len(floor) * len(COMPONENTS) == 5616
    assert len(sel + floor) * len(COMPONENTS) == 9828  # the spec's sweep-run count
    assert {cs.ref_seed for cs in sel if MAP[cs.map_id].value == "mean"} == {0}
    assert {cs.ref_seed for cs in sel if MAP[cs.map_id].value != "mean"} == {None}
    assert {cs.ref_seed for cs in floor} == {1, 2, 3, 4} and all(MAP[cs.map_id].value == "mean" for cs in floor)
    assert [cs.stem for cs in S.cell_sets(("ioi",), "selection", ("total_mean_frozen", "direct_zero"))] == [
        "total_mean_frozen_s0_r0", "direct_zero_s0"]
    with pytest.raises(ValueError):
        S.cell_sets(items, "nope")


def test_cell_spec():
    s = S.cell_spec(Head(5, 5), MAP["total_mean_frozen"], 3)
    assert (s.component_type, s.freeze_patterns, s.receiver, s.positions) == ("node", True, None, All())
    assert s.reference == MeanReference("corrupt", 2000, 3, "template") and s.direction == "ablate-clean"
    d = S.cell_spec(MLP(0), MAP["direct_zero"], None, positions=Labels(("END",)))
    assert (d.component_type, d.receiver, d.mlp_convention, d.freeze_patterns) == ("edge", Logits(), "wang", False)
    assert d.reference is None and d.positions == Labels(("END",))


def test_cell_set_record_matches_the_runner(tiny_model, tiny_battery, tmp_path):
    rec = run_tiny(tiny_model, tiny_battery, tmp_path, "total_resample_frozen")
    assert rec["components"] == ["L0H0", "L1H1", "L0.mlp"] and rec["complete"] is False
    assert rec["config"]["map"] == "total_resample_frozen" and rec["pre_registered"] is False
    prompts = S.load_prompts(tmp_path / "sweep" / "tiny" / "total_resample_frozen_s0.parquet")
    clean = S.load_clean(tmp_path / "sweep" / "tiny" / "clean_s0.parquet")
    for c in COMPS:
        direct = run(tiny_model, S.cell_spec(c, MAP["total_resample_frozen"], None), tiny_battery, 16, 0, False, 8)
        cell = rec["cells"][label(c)]
        assert cell["effect_mean"] == direct.aggregates["effect"]["ld"]["effect_mean"]
        assert cell["sem"] == direct.aggregates["effect"]["ld"]["sem"]
        assert prompts[label(c)]["ld_ablated"] == direct.columns["ld_ablated"].tolist()
        assert prompts[label(c)]["p_c_ablated"] == direct.columns["p_c_ablated"].tolist()
        assert clean["ld_clean"] == direct.columns["ld_clean"].tolist()
    assert json.loads((tmp_path / "sweep" / "tiny" / "total_resample_frozen_s0.json").read_text()) == rec


def test_direct_and_mean_cells(tiny_model, tiny_battery, tmp_path):
    rec = run_tiny(tiny_model, tiny_battery, tmp_path, "direct_mean", ref_seed=1, keep=False)
    assert rec["direct_effect_definition"] == "wang"
    cell = rec["cells"]["L1H1"]
    assert cell["spec"]["component_type"] == "edge" and cell["reference"]["n"] == 2000
    assert cell["reference"]["seed"] == 1
    assert not (tmp_path / "sweep" / "tiny" / "direct_mean_s0_r1.parquet").exists()  # aggregates only


def test_resume_skips_only_matching_cells(tiny_model, tiny_battery, tmp_path, monkeypatch):
    run_tiny(tiny_model, tiny_battery, tmp_path)
    calls = []
    real = S.runner.run

    def counting(*a, **k):
        calls.append(a[1].component)
        return real(*a, **k)

    monkeypatch.setattr(S.runner, "run", counting)
    run_tiny(tiny_model, tiny_battery, tmp_path)  # same spec, same rev: nothing reruns
    assert calls == []
    run_tiny(tiny_model, tiny_battery, tmp_path, comps=COMPS + (Head(1, 0),))  # one new cell
    assert calls == [Head(1, 0)]
    calls.clear()
    run_tiny(tiny_model, tiny_battery, tmp_path, rev="r2")  # code changed: rerun
    assert calls == list(COMPS)


def test_resume_refuses_a_different_config(tiny_model, tiny_battery, tmp_path):
    run_tiny(tiny_model, tiny_battery, tmp_path, n=16)
    with pytest.raises(S.SweepError, match="different config"):
        run_tiny(tiny_model, tiny_battery, tmp_path, n=8)


def test_clean_mismatch_is_a_hard_stop(tiny_model, tiny_battery, tmp_path):
    run_tiny(tiny_model, tiny_battery, tmp_path)
    path = tmp_path / "sweep" / "tiny" / "clean_s0.parquet"
    t = pq.read_table(path).to_pydict()
    t["ld_clean"][0] += 1.0
    pq.write_table(pa.table({"idx": pa.array(t["idx"], pa.int32()), "template": t["template"],
                             "ld_clean": pa.array(t["ld_clean"], pa.float32()),
                             "p_c_clean": pa.array(t["p_c_clean"], pa.float32())}), path)
    with pytest.raises(S.SweepError, match="clean pass differs"):
        run_tiny(tiny_model, tiny_battery, tmp_path, "total_zero_frozen")


def test_prompt_parquet_round_trip_and_order_check(tmp_path):
    prompts = {"L1H1": {"ld_ablated": [1.5, 2.5], "p_c_ablated": [0.25, 0.5]},
               "L0H0": {"ld_ablated": [0.5, -1.0], "p_c_ablated": [0.125, 0.75]}}
    path = tmp_path / "p.parquet"
    pq.write_table(S.prompts_table(prompts), path)
    assert S.load_prompts(path) == prompts
    assert pq.read_table(path).column("component").to_pylist() == ["L0H0", "L0H0", "L1H1", "L1H1"]  # COMPONENTS order
    pq.write_table(pa.table({"component": ["L0H0"], "idx": pa.array([1], pa.int32()), "ld_ablated": [0.0],
                             "p_c_ablated": [0.0]}), path)
    with pytest.raises(S.SweepError, match="not stored in order"):
        S.load_prompts(path)


def test_check_writable(monkeypatch):
    monkeypatch.setattr(S, "code_rev", lambda: ("abc", True))
    with pytest.raises(ValueError, match="uncommitted"):
        S.check_writable("results/E3", allow_dirty=False)
    with pytest.raises(ValueError, match="never writes under results"):
        S.check_writable("results/E3", allow_dirty=True)
    assert S.check_writable("scratch/E3", allow_dirty=True) == "abc"
    monkeypatch.setattr(S, "code_rev", lambda: ("def", False))
    assert S.check_writable("results/E3", allow_dirty=False) == "def"


@pytest.mark.parametrize("argv", [
    ["--item", "ioi", "--stage", "selection", "--maps", "total_nope"],
    ["--item", "ioi", "--stage", "selection", "--components", "L12H0"],
    ["--item", "ioi", "--stage", "selection", "--n", "0"],
    ["--item", "ioi", "--stage", "nope"],
])
def test_cli_refuses_before_the_model_loads(monkeypatch, argv):
    def boom(*a, **k):
        raise AssertionError("model loaded")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    monkeypatch.setattr(S, "code_rev", lambda: ("abc", False))
    with pytest.raises(SystemExit) as e:
        S.main(argv)
    assert e.value.code == 2


def test_cli_refuses_a_dirty_tree(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("model loaded")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    monkeypatch.setattr(S, "code_rev", lambda: ("abc", True))
    with pytest.raises(SystemExit) as e:
        S.main(["--item", "ioi", "--stage", "selection"])
    assert e.value.code == 2
