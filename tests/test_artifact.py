"""Artifact: one stem per distinct spec, a key per axis, JSON + parquet written and readable."""

import json

import pyarrow.parquet as pq
import pytest
import torch

from src.lesion import artifact
from src.lesion.runner import COLUMNS, run
from src.lesion.spec import MLP, AblationSpec, All, Head, Indices, Inputs, Labels, Logits, MeanReference


def spec(**kw):
    base = dict(component=Head(9, 9), value="zero", reference=None, component_type="node", receiver=None,
                mlp_convention=None, positions=All(), direction="ablate-clean", freeze_patterns=False)
    base.update(kw)
    return AblationSpec(**base)


REF = MeanReference("corrupt", 1000, 0, "template")


def test_stem_examples():
    assert artifact.stem(spec(component=Head(0, 0)), "ioi", 100000, 0, False) == \
        "ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0"
    assert artifact.stem(spec(component=MLP(0), value="mean", reference=REF), "ioi", 2000, 0, False) == \
        "ioi_L0mlp_mean-corrupt-n1000-s0-template_node_all_ablate-clean_n2000_seed0"
    assert artifact.stem(spec(component_type="edge", receiver=Logits(), mlp_convention="wang",
                              positions=Labels(("END", "S2")), freeze_patterns=False), "ioi", 10, 1, True) == \
        "ioi_L9H9_zero_edge-logits-wang_pos-END-S2_ablate-clean_n10_seed1_bos"
    assert "frozen" in artifact.stem(spec(freeze_patterns=True), "ioi", 1, 0, False)
    assert "edge-inputs-L10H7q-END+L11H10v-S2-term" in artifact.stem(
        spec(component_type="edge", receiver=Inputs(((10, 7, "q", "END"), (11, 10, "v", "S2"))), mlp_convention="term"),
        "ioi", 1, 0, False)


VARIANTS = [
    spec(), spec(component=Head(9, 8)), spec(component=MLP(9)), spec(value="resample"),
    spec(value="mean", reference=REF), spec(value="mean", reference=MeanReference("clean", 1000, 0, "template")),
    spec(value="mean", reference=MeanReference("corrupt", 999, 0, "template")),
    spec(value="mean", reference=MeanReference("corrupt", 1000, 1, "template")),
    spec(value="mean", reference=MeanReference("corrupt", 1000, 0, "pooled")),
    spec(component_type="edge", receiver=Logits(), mlp_convention="wang"),
    spec(component_type="edge", receiver=Logits(), mlp_convention="term"),
    spec(component_type="edge", receiver=Inputs(((10, 0, "q", "END"),)), mlp_convention="wang"),
    spec(positions=Labels(("END",))), spec(positions=Labels(("END", "S2"))), spec(positions=Indices((3,))),
    spec(direction="restore-clean"), spec(freeze_patterns=True),
]


def test_distinct_specs_get_distinct_stems():
    stems = [artifact.stem(s, "ioi", 100, 0, False) for s in VARIANTS]
    assert len(set(stems)) == len(stems)
    assert artifact.stem(spec(), "ioi", 100, 0, False) != artifact.stem(spec(), "ioi", 101, 0, False)
    assert artifact.stem(spec(), "ioi", 100, 0, False) != artifact.stem(spec(), "ioi", 100, 1, False)
    assert artifact.stem(spec(), "ioi", 100, 0, False) != artifact.stem(spec(), "ioi", 100, 0, True)
    assert artifact.stem(spec(), "ioi", 100, 0, False) != artifact.stem(spec(), "tiny", 100, 0, False)


@torch.no_grad()
def test_write_and_read_back(tiny_model, tiny_battery, tmp_path):
    s = spec(component=Head(0, 0), value="mean", reference=MeanReference("corrupt", 8, 1, "template"))
    result = run(tiny_model, s, tiny_battery, n=6, seed=0, prepend_bos=False, batch_size=4)
    env = artifact.environment_record(tiny_model, batch_size=4, seconds=result.seconds)
    record = artifact.build_record(result, s, tiny_battery, command="uv run python -m src.lesion.ablate --x",
                                   environment=env, cli_args={"x": 1, "freeze": False})
    jp, pp = artifact.write(record, result, tmp_path)
    assert jp == tmp_path / (artifact.stem(s, "tiny", 6, 0, False) + ".json") and pp.suffix == ".parquet"
    d = json.loads(jp.read_text())
    assert d["phase"] == "E1a" and d["command"].startswith("uv run python -m src.lesion.ablate")
    assert set(d["spec"]) >= {"granularity", "component_type", "value", "positions", "direction", "set",
                              "freeze_patterns", "mlp_convention"}
    assert d["environment"]["batch_size"] == 4 and "repo_commit" in d["environment"]
    assert d["environment"]["model"] == {"name": "gpt2", "revision": "607a30d783dfa663caf39e06633721c8d4cfcd7e"}
    assert set(d["environment"]["determinism"]) == {"use_deterministic_algorithms", "cudnn_deterministic",
                                                    "cudnn_benchmark", "cublas_workspace_config"}
    assert d["battery"]["corruption"] == {"name": "swap-2", "removes": "the token at position 2",
                                          "inserts": "a different token at position 2", "source": "tests/conftest.py"}
    assert d["battery"]["n"] == 6 and d["battery"]["seed"] == 0 and d["battery"]["prepend_bos"] is False
    assert d["reference"]["n"] == 8 and d["reference"]["per_template_counts"] == {"A": 4, "B": 4}
    assert d["destination_prompt"] == "clean" and d["direct_effect_definition"] is None
    assert d["cli"] == {"x": 1, "freeze": False}
    assert set(d["results"]) == {"clean", "ablated", "effect", "by_template"}
    table = pq.read_table(pp)
    assert table.num_rows == 6
    assert set(table.column_names) == {"idx", "template", *COLUMNS, "i"}
    assert table.column("idx").to_pylist() == list(range(6))
    assert table.column("ld_clean").to_pylist() == result.columns["ld_clean"].tolist()


@torch.no_grad()
def test_write_refuses_meta_key_collision(tiny_model, tiny_battery, tmp_path):
    s = spec(component=Head(0, 0), value="mean", reference=MeanReference("corrupt", 8, 1, "template"))
    result = run(tiny_model, s, tiny_battery, n=6, seed=0, prepend_bos=False, batch_size=4)
    env = artifact.environment_record(tiny_model, batch_size=4, seconds=result.seconds)
    record = artifact.build_record(result, s, tiny_battery, command="uv run python -m src.lesion.ablate --x",
                                   environment=env, cli_args={"x": 1, "freeze": False})
    result.meta = {"template": ["x"] * result.n}
    with pytest.raises(ValueError):
        artifact.write(record, result, tmp_path)


def test_direct_effect_definition_written():
    s = spec(component_type="edge", receiver=Logits(), mlp_convention="term")
    assert artifact.direct_effect_definition(s) == "term"
    assert artifact.direct_effect_definition(spec()) is None


@torch.no_grad()
def test_effect_sign_recorded_for_both_directions(tiny_model, tiny_battery, tmp_path):
    s = spec(component=Head(0, 0))  # ablate-clean
    result = run(tiny_model, s, tiny_battery, n=6, seed=0, prepend_bos=False, batch_size=4)
    env = artifact.environment_record(tiny_model, batch_size=4, seconds=result.seconds)
    record = artifact.build_record(result, s, tiny_battery, command="uv run python -m src.lesion.ablate --x",
                                   environment=env, cli_args={"x": 1, "freeze": False})
    assert record["effect_sign"] == (
        "positive = ablating the component hurt (clean minus intervened, on the clean prompt)")

    s = spec(component=Head(0, 0), direction="restore-clean")
    result = run(tiny_model, s, tiny_battery, n=6, seed=0, prepend_bos=False, batch_size=4)
    env = artifact.environment_record(tiny_model, batch_size=4, seconds=result.seconds)
    record = artifact.build_record(result, s, tiny_battery, command="uv run python -m src.lesion.ablate --x",
                                   environment=env, cli_args={"x": 1, "freeze": False})
    assert record["effect_sign"] == (
        "positive = restoring the clean value hurt; negative = restoration helped "
        "(unintervened minus intervened, on the corrupt prompt)")


from src.lesion.battery import Corruption  # noqa: E402
from tests.conftest import TinyBattery  # noqa: E402


def test_stem_scheme_suffix():
    assert artifact.stem(spec(), "ioi", 100, 0, False) == artifact.stem(spec(), "ioi", 100, 0, False, None)
    assert artifact.stem(spec(), "ioi", 100, 0, True, "flip") == \
        "ioi_L9H9_zero_node_all_ablate-clean_n100_seed0_bos_scheme-flip"


class OffDefaultTiny(TinyBattery):
    schemes = ("swap-2", "swap-2b")
    corruption = Corruption(name="swap-2b", removes="x", inserts="y", source="tests")


def _record(model, battery, tmp_path):
    s = spec(component=Head(0, 0))
    result = run(model, s, battery, n=6, seed=0, prepend_bos=False, batch_size=4)
    env = artifact.environment_record(model, batch_size=4, seconds=result.seconds)
    record = artifact.build_record(result, s, battery, command="c", environment=env, cli_args={})
    return record, result


@torch.no_grad()
def test_record_carries_expected_direction_and_schemes(tiny_model, tiny_battery, tmp_path):
    record, _ = _record(tiny_model, tiny_battery, tmp_path)
    assert record["expected_direction"] == "positive"
    assert record["battery"]["schemes"] == ["swap-2"]


@torch.no_grad()
def test_write_puts_off_default_scheme_in_the_stem(tiny_model, tiny_battery, tmp_path):
    rec_a, res_a = _record(tiny_model, tiny_battery, tmp_path)
    rec_b, res_b = _record(tiny_model, OffDefaultTiny(), tmp_path)
    ja, _ = artifact.write(rec_a, res_a, tmp_path)
    jb, _ = artifact.write(rec_b, res_b, tmp_path)
    assert ja != jb and jb.name.endswith("_scheme-swap-2b.json") and not ja.name.count("scheme-")


from src.lesion.knockout import KnockoutSetSpec, Member, run_set  # noqa: E402


@torch.no_grad()
def test_build_record_phase_default_and_override(tiny_model, tiny_battery):
    s = spec(component=Head(0, 0))
    res = run(tiny_model, s, tiny_battery, 4, 0, False, 4)
    assert artifact.build_record(res, s, tiny_battery, "cmd", {}, {})["phase"] == "E1a"
    assert artifact.build_record(res, s, tiny_battery, "cmd", {}, {}, phase="E2")["phase"] == "E2"


@torch.no_grad()
def test_set_record_stem_and_write(tmp_path, tiny_model, tiny_battery):
    ks = KnockoutSetSpec(members=(Member(Head(1, 0), Labels(("X",))),), complement=False, value="zero",
                         reference=None, direction="ablate-clean", freeze_patterns=False, granularity="heads")
    res = run_set(tiny_model, ks, tiny_battery, 4, 0, False, 4)
    rec = artifact.build_record(res, ks, tiny_battery, "cmd", {}, {}, phase="E2")
    assert rec["spec"]["set"]["members"][0]["head"] == {"layer": 1, "head": 0}
    assert rec["direct_effect_definition"] is None and rec["effect_sign"].startswith("positive = ablating")
    base = artifact.set_stem(ks, "tiny", "demo", 4, 0, False)
    assert base == "tiny_set-demo_zero_node_ablate-clean_n4_seed0"
    j, p = artifact.write(rec, res, tmp_path, base=base)
    assert j.name == base + ".json" and p.name == base + ".parquet"
    assert pq.read_table(p).num_rows == 4
    comp = KnockoutSetSpec(members=(), complement=True, value="mean", reference=REF, direction="ablate-clean",
                           freeze_patterns=True, granularity="heads")
    assert artifact.set_stem(comp, "ioi", "circuit", 2000, 0, True) == \
        "ioi_set-circuit-complement_mean-corrupt-n1000-s0-template_node_ablate-clean_frozen_n2000_seed0_bos"
