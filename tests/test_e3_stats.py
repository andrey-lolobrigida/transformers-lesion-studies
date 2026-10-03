"""E3 statistics on hand-worked values. Pure: no model, no files."""

import math
import statistics

import pytest

from src.lesion import e3_stats as S


def test_cell_s_zero_and_resample_is_the_sem():
    assert S.cell_s(0.02, None) == {"s": 0.02, "sem": 0.02, "ref_sd": None, "source": "sem"}


def test_cell_s_mean_takes_the_larger_of_sem_and_reference_spread():
    effects = [1.0, 1.1, 0.9, 1.0, 1.0]
    sd = statistics.stdev(effects)  # 0.0707...
    r = S.cell_s(0.01, effects)
    assert r == {"s": sd, "sem": 0.01, "ref_sd": sd, "source": "ref_seed_sd"}
    r = S.cell_s(0.5, effects)
    assert r["s"] == 0.5 and r["source"] == "sem"


@pytest.mark.parametrize("sem,ref", [(float("nan"), None), (0.1, [1.0, float("inf")]), (0.1, [1.0]), (-0.1, None)])
def test_cell_s_refuses(sem, ref):
    with pytest.raises(S.StatsError):
        S.cell_s(sem, ref)


def test_paired_sem_on_hand_values():
    # differences 1, 2, 3, 4: sd 1.2909944, sem = sd / 2
    assert math.isclose(S.paired_sem([2.0, 4.0, 6.0, 8.0], [1.0, 2.0, 3.0, 4.0]), statistics.stdev([1, 2, 3, 4]) / 2)
    assert S.paired_sem([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0
    with pytest.raises(S.StatsError):
        S.paired_sem([1.0, 2.0], [1.0])
    with pytest.raises(S.StatsError):
        S.paired_sem([1.0], [0.0])
    with pytest.raises(S.StatsError):
        S.paired_sem([1.0, float("nan")], [0.0, 0.0])


def test_z_test_and_the_first_holm_step():
    r = S.z_test(-3.0, 1.5)
    assert r["z"] == 2.0 and math.isclose(r["p"], 0.04550026389635842)
    first_step = 0.05 / 5616  # the spec's "first Holm step at z ~ 4.44"
    assert S.z_test(4.45, 1.0)["p"] < first_step < S.z_test(4.44, 1.0)["p"]


@pytest.mark.parametrize("effect,s", [(float("nan"), 1.0), (1.0, float("inf")), (1.0, 0.0), (1.0, -1.0)])
def test_z_test_refuses(effect, s):
    with pytest.raises(S.StatsError):
        S.z_test(effect, s)


def test_holm_hand_worked():
    # m = 4, alpha 0.05: thresholds 0.0125, 0.01667, 0.025, 0.05.
    # Sorted: d 0.005 <= 0.0125 reject; a 0.01 <= 0.01667 reject; c 0.03 > 0.025 stop; b not rejected.
    h = S.holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005}, 0.05)
    assert {k: v["reject"] for k, v in h.items()} == {"a": True, "b": False, "c": False, "d": True}
    assert [h[k]["step"] for k in "dacb"] == [1, 2, 3, 4]
    assert math.isclose(h["d"]["threshold"], 0.0125) and math.isclose(h["b"]["threshold"], 0.05)


def test_holm_stops_at_the_first_failure():
    # m = 3: thresholds 0.01667, 0.025, 0.05. a fails step 1, so c (0.04 < 0.05) is not rejected either.
    h = S.holm({"a": 0.02, "b": 0.03, "c": 0.04}, 0.05)
    assert not any(v["reject"] for v in h.values())


def test_holm_ties_extremes_and_refusals():
    h = S.holm({"b": 0.01, "a": 0.01}, 0.05)
    assert h["a"]["step"] == 1 and h["b"]["step"] == 2 and h["a"]["reject"] and h["b"]["reject"]
    assert not any(v["reject"] for v in S.holm({k: 0.9 for k in "abc"}, 0.05).values())
    assert all(v["reject"] for v in S.holm({k: 0.0 for k in "abc"}, 0.05).values())
    assert S.holm({}, 0.05) == {}
    for bad in (float("nan"), -0.1, 1.5):
        with pytest.raises(S.StatsError):
            S.holm({"a": bad}, 0.05)


def test_select_rule_a_keeps_sign_and_ignores_uncleared_cells():
    cells = {f"c{i}": {"effect": float(i) * (-1 if i % 2 else 1), "reject": True} for i in range(1, 15)}
    cells["big_not_cleared"] = {"effect": 100.0, "reject": False}
    r = S.select_rule_a(cells, 10)
    assert [x["component"] for x in r["selected"]] == [f"c{i}" for i in range(14, 4, -1)]
    assert r["selected"][0] == {"component": "c14", "effect": 14.0, "rank": 1}
    assert r["selected"][1] == {"component": "c13", "effect": -13.0, "rank": 2}
    assert r["n_cleared"] == 14 and r["tie_at_cut"] is False and "big_not_cleared" not in r["ranks"]


def test_select_rule_a_tie_straddling_k_counts_inside():
    cells = {f"c{i}": {"effect": 10.0 - i, "reject": True} for i in range(9)}  # ranks 1..9
    cells["t1"] = {"effect": 1.0, "reject": True}
    cells["t2"] = {"effect": -1.0, "reject": True}  # |effect| ties t1: both rank 10
    r = S.select_rule_a(cells, 10)
    assert len(r["selected"]) == 11 and r["tie_at_cut"] is True
    assert r["ranks"]["t1"] == r["ranks"]["t2"] == 10


def test_select_rule_a_fewer_than_k_and_none():
    cells = {"a": {"effect": 1.0, "reject": True}, "b": {"effect": 2.0, "reject": True},
             "c": {"effect": 9.0, "reject": False}}
    assert [x["component"] for x in S.select_rule_a(cells, 10)["selected"]] == ["b", "a"]
    r = S.select_rule_a({"c": {"effect": 9.0, "reject": False}}, 10)
    assert r["selected"] == [] and r["n_cleared"] == 0 and r["tie_at_cut"] is False
    with pytest.raises(S.StatsError):
        S.select_rule_a({"a": {"effect": float("nan"), "reject": True}}, 10)


def test_fraction_restored():
    assert S.fraction_restored(-1.5, 0.75, 3.0) == {"fraction_restored": 0.5, "fraction_sem": 0.25}
    with pytest.raises(S.StatsError):
        S.fraction_restored(-1.5, 0.3, 0.0)
    with pytest.raises(S.StatsError):
        S.fraction_restored(float("nan"), 0.3, 3.0)
