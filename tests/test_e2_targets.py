"""E2 target helpers on the tiny model: sweeps and resume, set artifacts,
summaries and arithmetic. The target functions themselves run on GPT-2 in
Task 8's smoke run."""

import json

import pytest
import torch

from src.lesion import e2_reproduce as R
from src.lesion import e2_targets as T
from src.lesion.e2_reproduce import Sweep
from src.lesion.knockout import Member
from src.lesion.runner import run
from src.lesion.spec import Head, Labels, Logits, SpecError

CANDS = (Head(0, 0), Head(0, 1), Head(1, 0), Head(1, 1))
SWEEP = Sweep("tiny", "END", Logits(), "tests")


def ctx(model, tmp_path, n=6, resume=False, pre=False):
    return T.Ctx(model=model, tok=None, n=n, seed=0, batch_size=4, out_dir=tmp_path, command="test", cli={},
                 pre_registered=pre, resume=resume)


@torch.no_grad()
def test_sweep_rows_equal_single_runs(tiny_model, tiny_battery, tmp_path):
    rec = T.run_sweep(ctx(tiny_model, tmp_path), tiny_battery, SWEEP, "resample", False, tmp_path / "s.json",
                      candidates=CANDS)
    assert [r["sender"] for r in rec["rows"]] == ["L0H0", "L0H1", "L1H0", "L1H1"]
    for h, row in zip(CANDS, rec["rows"]):
        e = run(tiny_model, T.edge_spec(h, "resample", "END", Logits()), tiny_battery, 6, 0, False, 4) \
            .aggregates["effect"]["ld"]
        assert row["effect_mean"] == e["effect_mean"] and row["sem"] == e["sem"]
    assert rec["pre_registered"] is False
    assert json.loads((tmp_path / "s.json").read_text())["config"] == rec["config"]
    assert T.sweep_scores(rec) == {r["sender"]: r["effect_mean"] for r in rec["rows"]}


def test_sweep_resume_reuses_only_a_matching_file(tiny_model, tiny_battery, tmp_path, monkeypatch):
    path = tmp_path / "s.json"
    T.run_sweep(ctx(tiny_model, tmp_path), tiny_battery, SWEEP, "zero", False, path, candidates=CANDS)

    def boom(*a, **k):
        raise AssertionError("recomputed")

    monkeypatch.setattr(T, "run", boom)
    again = T.run_sweep(ctx(tiny_model, tmp_path, resume=True), tiny_battery, SWEEP, "zero", False, path,
                        candidates=CANDS)
    assert len(again["rows"]) == 4
    with pytest.raises(AssertionError, match="recomputed"):  # a different n is a different sweep
        T.run_sweep(ctx(tiny_model, tmp_path, n=8, resume=True), tiny_battery, SWEEP, "zero", False, path,
                    candidates=CANDS)
    with pytest.raises(AssertionError, match="recomputed"):  # pre-registration status must match too
        T.run_sweep(ctx(tiny_model, tmp_path, resume=True, pre=True), tiny_battery, SWEEP, "zero", False, path,
                    candidates=CANDS)
    with pytest.raises(AssertionError, match="recomputed"):  # without --resume nothing is reused
        T.run_sweep(ctx(tiny_model, tmp_path), tiny_battery, SWEEP, "zero", False, path, candidates=CANDS)


def test_edge_spec_refuses_an_empty_path():
    with pytest.raises(SpecError):
        T.edge_spec(Head(4, 11), "resample", "S1+1", R.I2_ROUTES[1].receiver)
    s = T.edge_spec(Head(4, 11), "mean", "S1+1", R.I2_ROUTES[0].receiver)
    assert s.mlp_convention == "wang" and s.reference.n == R.REF_N and s.positions == Labels(("S1+1",))


@torch.no_grad()
def test_set_run_artifact_and_summary(tiny_model, tiny_battery, tmp_path):
    c = ctx(tiny_model, tmp_path, pre=True)
    rec = T.run_set_named(c, T.set_spec([Member(Head(1, 0), Labels(("X",)))], "zero"), tiny_battery, False,
                          tmp_path / "d", "demo")
    assert rec["phase"] == "E2" and rec["pre_registered"] is True
    assert rec["spec"]["set"]["members"] == [{"head": {"layer": 1, "head": 0},
                                             "positions": {"kind": "labels", "labels": ["X"]}}]
    assert (tmp_path / "d" / "tiny_set-demo_zero_node_ablate-clean_n6_seed0.json").exists()
    s = T.summary(rec)
    assert s["ref_n"] is None and s["value"] == "zero" and s["n"] == 6
    assert s["effect_mean"] == rec["results"]["effect"]["ld"]["effect_mean"]
    m = T.summary(T.run_set_named(c, T.set_spec([Member(Head(1, 0), Labels(("X",)))], "mean", ref_n=8),
                                  tiny_battery, False, tmp_path / "d", "demo"))
    assert m["ref_n"] == 8 and m["ref_per_template_counts"] == {"A": 4, "B": 4}


@torch.no_grad()
def test_run_single_writes_a_pre_registered_flag(tiny_model, tiny_battery, tmp_path):
    rec = T.run_single(ctx(tiny_model, tmp_path), T.node_spec(Head(0, 1), "zero", Labels(("X",))), tiny_battery,
                       False, tmp_path / "s")
    assert rec["pre_registered"] is False and rec["phase"] == "E2"
    assert len(list((tmp_path / "s").glob("*.json"))) == 1


@torch.no_grad()
def test_gap_stats(tiny_model, tiny_battery, tmp_path):
    g = T.gap_stats(ctx(tiny_model, tmp_path), tiny_battery, False)
    assert set(g) == {"n", "mean_ld_clean", "mean_ld_corrupt", "gap", "fraction_removed"} and g["n"] == 6
    assert g["gap"] == pytest.approx(g["mean_ld_clean"] - g["mean_ld_corrupt"], abs=1e-6)


def test_fraction_restored():
    assert T.fraction_restored(ablated_mean=2.0, corrupt_mean=0.0, gap=4.0) == 0.5
    assert T.fraction_restored(-1.0, 0.0, 4.0) == -0.25


def test_below_template_floor():
    assert T.below_template_floor({"A": 29, "B": 40})
    assert not T.below_template_floor({"A": 30, "B": 31})


def test_every_target_has_a_function():
    assert set(T.TARGET_FUNCS) == set(R.TARGETS)
