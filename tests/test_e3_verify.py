"""E3 verification: the row builders on hand values, the arms on the tiny
model, the baseline check, and CLI refusals. CPU, offline."""

import json
import math

import pytest

from src.lesion import e3_verify as V
from src.lesion.e3_prereg import MAP
from src.lesion.e3_sweep import cell_spec
from src.lesion.knockout import KnockoutSetSpec, Member, run_set
from src.lesion.runner import run
from src.lesion.spec import All, Head, Labels


def sel(id_, effect, s=0.1, rank=1):
    item, map_id, comp = id_.split("/")
    return {"id": id_, "item": item, "map": map_id, "component": comp, "effect": effect, "s": s, "rank": rank}


def test_replication_rows():
    sels = [sel("ioi/total_zero_unfrozen/L9H6", 2.0), sel("ioi/total_zero_unfrozen/L9H9", 1.0, rank=2),
            sel("ioi/direct_mean/L10H7", -1.0, rank=1), sel("ioi/total_zero_unfrozen/L4H11", 0.5, rank=3)]
    held = {"ioi/total_zero_unfrozen/L9H6": {"effect": 1.9, "sem": 0.1, "ref_effects": None},  # same sign, clears
            "ioi/total_zero_unfrozen/L9H9": {"effect": -1.0, "sem": 0.1, "ref_effects": None},  # sign flipped
            "ioi/direct_mean/L10H7": {"effect": -0.9, "sem": 0.01, "ref_effects": [-0.9, -0.5, -1.3, -0.9, -0.9]},
            "ioi/total_zero_unfrozen/L4H11": {"effect": 0.1, "sem": 0.1, "ref_effects": None}}  # does not clear
    rows = {r["id"]: r for r in V.replication_rows(sels, held, "verify_confirmatory")}
    assert rows["ioi/total_zero_unfrozen/L9H6"]["verdict"] == "replicated"
    assert rows["ioi/total_zero_unfrozen/L9H9"]["verdict"] == "not replicated"
    assert rows["ioi/total_zero_unfrozen/L9H9"]["held_out"]["reject"] is True  # clears, wrong sign
    mean_row = rows["ioi/direct_mean/L10H7"]["held_out"]
    assert mean_row["source"] == "ref_seed_sd" and math.isclose(mean_row["z"], 0.9 / mean_row["ref_sd"])
    assert rows["ioi/total_zero_unfrozen/L4H11"]["verdict"] == "not replicated"
    assert all(r["family"] == "verify_confirmatory" for r in rows.values())
    assert rows["ioi/total_zero_unfrozen/L9H9"]["selection_rank"] == 2


def test_sufficiency_rows():
    runs = [{"id": "ioi/L9H6", "kind": "single", "item": "ioi", "components": ["L9H6"], "effect": -1.5, "sem": 0.05,
             "gap": 3.0},
            {"id": "ioi/L0H1", "kind": "single", "item": "ioi", "components": ["L0H1"], "effect": -0.01, "sem": 0.05,
             "gap": 3.0}]
    rows = {r["id"]: r for r in V.sufficiency_rows(runs, "sufficiency_confirmatory")}
    assert rows["ioi/L9H6"]["fraction_restored"] == 0.5 and rows["ioi/L9H6"]["reject"] is True
    assert rows["ioi/L0H1"]["reject"] is False and rows["ioi/L0H1"]["family"] == "sufficiency_confirmatory"


def test_adversarial_units_dedupe_and_cover_six_maps():
    conf = [sel("induction/total_zero_frozen/L5H5", 3.0), sel("induction/direct_zero/L7H2", 1.0),
            sel("ioi/total_zero_unfrozen/L9H6", 2.0)]
    expl = [{**sel("induction/total_mean_unfrozen/L5H1", 0.4), "why": "x"}]
    units = V.adversarial_units(conf, expl)
    keys = [(u["unit"], u["map"]) for u in units]
    assert len(keys) == len(set(keys)) == 4 * 6 + 6 + 1 + 1  # I3 singles, the set; L5H5 merges; L7H2; L5H1
    l5h5 = next(u for u in units if (u["unit"], u["map"]) == ("L5H5", "total_zero_frozen"))
    assert l5h5["sources"] == ["E2 I3", "confirmatory"]
    assert ("set:L5H5+L6H9", "total_resample_frozen") in keys
    assert not any(u["unit"] == "L9H6" for u in units)  # IOI selections are not induction


def test_run_arm_single_and_set_on_the_tiny_model(tiny_model, tiny_battery):
    ctx = V.Ctx(model=tiny_model, tok=None, n=16, batch_size=8, root=None, rev="r", command="t", pre_registered=False)
    batteries = {"fresh_prefix": tiny_battery, "shuffle_prefix": tiny_battery}
    unit = {"unit": "L1H1", "members": ["L1H1"], "map": "total_zero_frozen", "sources": ["E2 I3"]}
    a = V.run_arm(ctx, unit, "end_only", batteries)
    direct = run(tiny_model, cell_spec(Head(1, 1), MAP["total_zero_frozen"], None, positions=Labels(("END",))),
                 tiny_battery, 16, 0, True, 8)
    assert a["effect"] == direct.aggregates["effect"]["ld"]["effect_mean"] and a["ref_effects"] is None
    assert a["positions"] == "END" and a["scheme"] == "fresh_prefix"
    s = {"unit": "set:L0H0+L1H1", "members": ["L0H0", "L1H1"], "map": "total_resample_unfrozen", "sources": ["E2 I3"]}
    b = V.run_arm(ctx, s, "baseline", batteries)
    ks = KnockoutSetSpec(members=(Member(Head(0, 0), All()), Member(Head(1, 1), All())), complement=False,
                         value="resample", reference=None, direction="ablate-clean", freeze_patterns=False,
                         granularity="heads")
    assert b["effect"] == run_set(tiny_model, ks, tiny_battery, 16, 0, True, 8).aggregates["effect"]["ld"]["effect_mean"]


def test_run_arm_mean_uses_reference_seeds_0_to_4(tiny_model, tiny_battery):
    ctx = V.Ctx(model=tiny_model, tok=None, n=16, batch_size=8, root=None, rev="r", command="t", pre_registered=False)
    unit = {"unit": "L0H0", "members": ["L0H0"], "map": "total_mean_unfrozen", "sources": ["E2 I3"]}
    a = V.run_arm(ctx, unit, "baseline", {"fresh_prefix": tiny_battery})
    assert len(a["ref_effects"]) == 5 and a["effect"] == a["ref_effects"][0] and a["reference"]["seed"] == 0


def test_adversarial_rows():
    arms = [{"unit": "L5H5", "map": "total_zero_unfrozen", "arm": "baseline", "effect": 3.0, "sem": 0.1,
             "ref_effects": None},
            {"unit": "L5H5", "map": "total_zero_unfrozen", "arm": "shuffle_prefix", "effect": -0.5, "sem": 0.1,
             "ref_effects": None},
            {"unit": "L5H5", "map": "total_zero_unfrozen", "arm": "end_only", "effect": 2.5, "sem": 0.1,
             "ref_effects": None}]
    rows = {r["arm"]: r for r in V.adversarial_rows(arms)}
    assert rows["baseline"].get("reject") is None
    assert rows["shuffle_prefix"]["sign_vs_baseline"] == "flipped" and rows["shuffle_prefix"]["reject"] is True
    assert rows["end_only"]["sign_vs_baseline"] == "same" and rows["end_only"]["baseline_effect"] == 3.0


def test_baseline_must_reproduce_the_sweep_cell(tmp_path):
    d = tmp_path / "sweep" / "induction"
    d.mkdir(parents=True)
    (d / "total_zero_frozen_s0.json").write_text(json.dumps({"cells": {"L5H5": {"effect_mean": 3.0}}}))
    row = {"unit": "L5H5", "members": ["L5H5"], "map": "total_zero_frozen", "arm": "baseline", "effect": 3.0}
    V.check_baseline(tmp_path, row)
    with pytest.raises(V.VerifyError, match="does not reproduce"):
        V.check_baseline(tmp_path, {**row, "effect": 3.0000001})
    V.check_baseline(tmp_path, {**row, "unit": "set:L5H5+L6H9", "members": ["L5H5", "L6H9"], "effect": 9.0})  # sets skip


def test_exit_rows():
    repl = [{"id": "induction/total_zero_frozen/L5H5", "item": "induction", "map": "total_zero_frozen",
             "component": "L5H5", "effect": 3.0, "s": 0.1, "selection_rank": 1,
             "held_out": {"effect": 2.9, "s": 0.1, "z": 29.0, "reject": True}, "verdict": "replicated"}]
    restore = [{"id": "induction/L5H5", "kind": "single", "fraction_restored": 0.02, "fraction_sem": 0.001,
                "z": 3.0, "reject": False}]
    adv = [{"unit": "L5H5", "map": "total_zero_frozen", "arm": "shuffle_prefix", "effect": 0.1, "s": 0.05,
            "reject": False, "sign_vs_baseline": "same"}]
    row = V.exit_rows(repl, restore, adv)[0]
    assert row["verdict"] == "replicated" and row["restore"]["fraction_restored"] == 0.02
    assert row["adversarial"]["shuffle_prefix"]["reject"] is False and row["adversarial"]["end_only"] is None


@pytest.mark.parametrize("argv", [["--stage", "replicate"], ["--stage", "restore"], ["--stage", "nope"],
                                  ["--stage", "replicate", "--n", "0"]])
def test_cli_refuses_before_the_model_loads(monkeypatch, tmp_path, argv):
    def boom(*a, **k):
        raise AssertionError("model loaded")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    monkeypatch.setattr("src.lesion.e3_sweep.code_rev", lambda: ("abc", False))
    with pytest.raises(SystemExit) as e:
        V.main(argv + ["--out-root", str(tmp_path)])  # no committed lists under tmp_path
    assert e.value.code == 2


def test_adversarial_sign_is_zero_when_an_effect_is_exactly_zero():
    arms = [{"unit": "L5H5", "map": "total_zero_unfrozen", "arm": "baseline", "effect": 3.0, "sem": 0.1,
             "ref_effects": None},
            {"unit": "L5H5", "map": "total_zero_unfrozen", "arm": "end_only", "effect": 0.0, "sem": 0.1,
             "ref_effects": None}]
    rows = {r["arm"]: r for r in V.adversarial_rows(arms)}
    assert rows["end_only"]["sign_vs_baseline"] == "zero"


def test_persisted_arms_are_reused_only_for_the_same_code_rev(tmp_path):
    p = tmp_path / "arms.jsonl"
    good = {"unit": "L5H5", "map": "m", "arm": "baseline", "effect": 1.0, "code_rev": "abc"}
    stale = {"unit": "L5H5", "map": "m", "arm": "end_only", "effect": 2.0, "code_rev": "old"}
    p.write_text(json.dumps(good) + "\n" + json.dumps(stale) + "\n")
    got = V.load_persisted_arms(p, "abc")
    assert list(got) == [("L5H5", "m", "baseline")] and "code_rev" not in got[("L5H5", "m", "baseline")]
    assert V.load_persisted_arms(tmp_path / "missing.jsonl", "abc") == {}
