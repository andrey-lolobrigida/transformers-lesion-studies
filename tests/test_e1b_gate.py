"""Gate statistics, verdicts and the measurement pass, on hand values and the tiny model."""

import json

import pyarrow.parquet as pq
import pytest
import torch

from src.lesion import e1b_gate as g
from src.lesion.runner import run
from src.lesion.spec import AblationSpec, All, Head


def test_thresholds_are_the_pre_registered_ones():
    assert (g.ACC_MIN, g.GAP_MIN, g.SURVIVORS_MIN) == (0.90, 1.0, 300)
    assert (g.REF_N, g.REF_SEED, g.DEFAULT_N) == (1000, 0, 2000)
    assert g.THRESHOLDS == {"pairwise_accuracy_min": 0.90, "gap_min": 1.0, "survivors_min": 300, "template_floor": 30}


def test_statistics_on_hand_values():
    cols = {"ld_clean": torch.tensor([2., 4., -1., 3.]), "ld_corrupt": torch.tensor([0., 1., 0., 1.]),
            "p_c_clean": torch.tensor([.5, .5, .5, .5]), "p_c_corrupt": torch.tensor([.25, .25, .25, .25]),
            "top1_clean": torch.tensor([1., 0., 0., 1.])}
    st = g.statistics(cols, ["A", "A", "B", "B"])
    assert st["n"] == 4 and st["pairwise_accuracy"] == 0.75 and st["top1_rate"] == 0.5
    assert st["clean"]["mean_ld"] == pytest.approx(2.0) and st["corrupt"]["mean_ld"] == pytest.approx(0.5)
    assert st["clean"]["mean_p_c"] == pytest.approx(0.5) and st["corrupt"]["mean_p_c"] == pytest.approx(0.25)
    assert st["gap"] == pytest.approx(1.5) and st["fraction_removed"] == pytest.approx(0.75)
    assert st["gap_sem"] == pytest.approx(torch.tensor([2., 3., -1., 2.]).std().item() / 2)
    assert st["clean"]["std_ld"] == pytest.approx(torch.tensor([2., 4., -1., 3.]).std().item())
    assert st["by_template"]["A"] == {"n": 2, "mean_ld_clean": pytest.approx(3.0), "mean_ld_corrupt": pytest.approx(0.5)}


def test_pairwise_accuracy_is_an_exact_ratio():
    ld = torch.tensor([1.] * 1800 + [-1.] * 200)
    cols = {"ld_clean": ld, "ld_corrupt": ld * 0, "p_c_clean": ld * 0, "p_c_corrupt": ld * 0, "top1_clean": ld * 0}
    assert g.statistics(cols, ["A"] * 2000)["pairwise_accuracy"] == 0.9  # not 0.8999999761581421


def test_verdict_thresholds_are_inclusive():
    v = g.verdict({"pairwise_accuracy": 0.90, "gap": 1.0}, survivors=None)
    assert v["pass"] and set(v["conditions"]) == {"pairwise_accuracy", "gap"}
    assert v["conditions"]["gap"] == {"value": 1.0, "threshold": 1.0, "pass": True}
    assert not g.verdict({"pairwise_accuracy": 0.8999, "gap": 5.0}, None)["pass"]
    assert not g.verdict({"pairwise_accuracy": 1.0, "gap": 0.999}, None)["pass"]
    v = g.verdict({"pairwise_accuracy": 1.0, "gap": 5.0}, survivors=299)
    assert not v["pass"] and v["conditions"]["survivors"] == {"value": 299, "threshold": 300, "pass": False}
    assert g.verdict({"pairwise_accuracy": 1.0, "gap": 5.0}, survivors=300)["pass"]
    v = g.verdict(None, survivors=0)
    assert not v["pass"] and v["conditions"]["gap"]["value"] is None


@torch.no_grad()
def test_measure_matches_the_harness_passes(tiny_model, tiny_battery):
    cols, templates = g.measure(tiny_model, tiny_battery, n=8, seed=0, prepend_bos=False, batch_size=4)
    assert templates == [p.template for p in tiny_battery.pairs(8, 0, False)]
    kw = dict(component=Head(0, 0), value="zero", reference=None, component_type="node", receiver=None,
              mlp_convention=None, positions=All(), freeze_patterns=False)
    a = run(tiny_model, AblationSpec(direction="ablate-clean", **kw), tiny_battery, 8, 0, False, 4)
    r = run(tiny_model, AblationSpec(direction="restore-clean", **kw), tiny_battery, 8, 0, False, 4)
    assert torch.equal(cols["ld_clean"], a.columns["ld_clean"])
    assert torch.equal(cols["p_c_clean"], a.columns["p_c_clean"])
    assert torch.equal(cols["ld_corrupt"], r.columns["ld_clean"])  # restore-clean's *_clean = corrupt, unintervened
    assert set(cols) == {"ld_clean", "ld_corrupt", "p_c_clean", "p_c_corrupt", "top1_clean"}
    assert set(cols["top1_clean"].tolist()) <= {0.0, 1.0}


def test_reference_floor_reports_small_templates(tiny_battery):
    f = g.reference_floor(tiny_battery, ref_n=10, prepend_bos=False)
    assert f == {"ref_n": 10, "ref_seed": 0, "floor": 30, "per_template_counts": {"A": 5, "B": 5}, "min": 5,
                 "templates_below_floor": ["A", "B"]}


def test_write_json_and_parquet(tiny_battery, tmp_path):
    cols = {"ld_clean": torch.tensor([1., 2.]), "ld_corrupt": torch.tensor([0., 0.])}
    jp = g.write({"x": 1}, cols, ["A", "B"], tmp_path, "tiny", "swap-2")
    assert jp == tmp_path / "tiny" / "swap-2.json" and json.loads(jp.read_text()) == {"x": 1}
    t = pq.read_table(jp.with_suffix(".parquet"))
    assert t.column_names == ["idx", "template", "ld_clean", "ld_corrupt"] and t.num_rows == 2
    jp = g.write({"x": 2}, None, [], tmp_path, "tiny", "empty")
    assert not jp.with_suffix(".parquet").exists()


def test_battery_record(tiny_battery):
    r = g.battery_record(tiny_battery, 8, 0, False)
    assert r["schemes"] == ["swap-2"] and r["expected_direction"] == "positive" and r["corruption"]["name"] == "swap-2"
    assert (r["n"], r["seed"], r["prepend_bos"]) == (8, 0, False)


@pytest.fixture
def never_load_model(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("model loaded before validation finished")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    monkeypatch.setattr("src.lesion.model.plain_tokenizer", boom)


@pytest.mark.parametrize("argv", [
    ["--item", "all", "--scheme", "flip"],        # a scheme only makes sense for one item
    ["--item", "ioi", "--scheme", "nope"],         # unknown scheme
    ["--item", "ioi", "--prepend-bos", "maybe"],   # bad bool
])
def test_refusals_exit_2_before_model_loads(never_load_model, argv):
    with pytest.raises(SystemExit) as e:
        g.main(argv)
    assert e.value.code == 2
