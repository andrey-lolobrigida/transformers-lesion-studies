"""E3 validation gates: the comparison helpers on hand-built records, and the
CLI's refusals. The gates themselves run on the GPU in Task 10."""

import pytest

from src.lesion import e3_gates as G


def floor_record():
    return {"rows": [{"component": "L0.mlp", "effect_mean_by_ref_seed": {"0": 1.0, "1": 1.1}, "sem_seed0": 0.05},
                     {"component": "L3H0", "effect_mean_by_ref_seed": {"0": -0.2, "1": -0.3}, "sem_seed0": 0.01}]}


def recs(**over):
    cells0 = {"L0.mlp": {"effect_mean": 1.0, "sem": 0.05}, "L3H0": {"effect_mean": -0.2, "sem": 0.01}}
    cells1 = {"L0.mlp": {"effect_mean": 1.1, "sem": 0.07}, "L3H0": {"effect_mean": -0.3, "sem": 0.02}}
    for (rs, lab, key), v in over.items():
        (cells0 if rs == 0 else cells1)[lab][key] = v
    return {0: {"cells": cells0}, 1: {"cells": cells1}}


def test_compare_floor_bitwise():
    compared, mismatches = G.compare_floor(floor_record(), recs())
    assert compared == 6 and mismatches == []  # 2 components x (2 seeds + seed-0 sem)


def test_compare_floor_reports_every_mismatch():
    r = recs()
    r[1]["cells"]["L3H0"]["effect_mean"] = -0.30000000000000004  # one ulp off still fails
    r[0]["cells"]["L0.mlp"]["sem"] = 0.051
    compared, mismatches = G.compare_floor(floor_record(), r)
    assert compared == 6
    assert {(m["component"], m["field"]) for m in mismatches} == {("L3H0", "effect_mean@ref1"), ("L0.mlp", "sem@ref0")}


def test_compare_columns():
    ours = {"ld_clean": [1.0, 2.0], "ld_ablated": [0.5, 0.25]}
    assert G.compare_columns(ours, {"ld_clean": [1.0, 2.0], "ld_ablated": [0.5, 0.25]}, "x") == (2, [])
    compared, mismatches = G.compare_columns(ours, {"ld_clean": [1.0, 2.0], "ld_ablated": [0.5, 0.26]}, "x")
    assert compared == 2 and mismatches == [{"where": "x", "column": "ld_ablated", "first_diff_at": 1,
                                             "ours": 0.25, "theirs": 0.26}]
    compared, mismatches = G.compare_columns({"ld_clean": [1.0]}, {"ld_clean": [1.0, 2.0]}, "y")
    assert mismatches[0]["first_diff_at"] == "length 1 vs 2"


def test_cli_refuses_a_dirty_tree_before_the_model_loads(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("model loaded")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    monkeypatch.setattr("src.lesion.e3_sweep.code_rev", lambda: ("abc", True))
    with pytest.raises(SystemExit) as e:
        G.main(["--gate", "all"])
    assert e.value.code == 2
    with pytest.raises(SystemExit):
        G.main(["--gate", "4"])
