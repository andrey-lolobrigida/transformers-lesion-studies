"""E3 selection on a fake sweep: the family has 5,616 tests, s follows the
spec's table, layer-11 frozen deltas are exact zeros, rule A picks what it
should, and the list checks refuse what they should. No model."""

import json
import math
import statistics
import subprocess

import pyarrow.parquet as pq
import pytest

from src.lesion import e3_select as E
from src.lesion.e3_prereg import COMPONENTS, ITEM, MAP, N_FAMILY, label
from src.lesion.e3_sweep import cell_sets, prompts_table, stage_dir

NP = 6  # prompts per fake cell


def zero_effect(item, map_id, lab, rs):
    return 0.0


def fake_root(root, effect=zero_effect, sem=0.01):
    """Complete fake records for every selection and floor cell set. Frozen maps
    get per-prompt ld offset by 0.5 on odd prompts, except layer-11 components,
    which (as in the model) get identical frozen and unfrozen columns."""
    for stage in ("selection", "floor"):
        for cs in cell_sets(tuple(ITEM), stage):
            d = stage_dir(root, stage, cs.item)
            d.mkdir(parents=True, exist_ok=True)
            cells = {label(c): {"effect_mean": effect(cs.item, cs.map_id, label(c), cs.ref_seed), "sem": sem}
                     for c in COMPONENTS}
            rec = {"pre_registered": True, "complete": True, "components": list(cells), "cells": cells}
            (d / f"{cs.stem}.json").write_text(json.dumps(rec))
            if stage == "selection":
                frozen = MAP[cs.map_id].frozen
                prompts = {lab: {"ld_ablated": [k + (0.5 * (k % 2) if frozen and not lab.startswith("L11") else 0.0)
                                                for k in range(NP)], "p_c_ablated": [0.5] * NP} for lab in cells}
                pq.write_table(prompts_table(prompts), d / f"{cs.stem}.parquet")
    return root


def by_id(tests):
    return {t["id"]: t for t in tests}


def test_family_size_and_kinds(tmp_path):
    tests = E.build_tests(fake_root(tmp_path))
    assert len(tests) == N_FAMILY == 5616
    assert [sum(t["kind"] == k for t in tests) for k in ("total", "direct", "delta")] == [2808, 1404, 1404]
    assert len({t["id"] for t in tests}) == 5616


def test_exact_zero_deltas_are_recorded_not_tested(tmp_path):
    tests = E.build_tests(fake_root(tmp_path))
    exact = [t for t in tests if not t["tested"]]
    assert len(exact) == 13 * 3 * 3  # layer-11 heads and MLP, three items, three values
    assert all(t["kind"] == "delta" and t["component"].startswith("L11") for t in exact)
    assert all(t["p"] == 1.0 and t["z"] is None and t["source"] == "exact_zero" and not t["reject"] for t in exact)
    t = by_id(tests)["ioi/delta_zero/L10H3"]
    assert t["tested"] and math.isclose(t["s"], statistics.stdev([0.5 * (k % 2) for k in range(NP)]) / math.sqrt(NP))


def test_a_planted_effect_is_rejected_and_selected(tmp_path):
    def effect(item, map_id, lab, rs):
        return 5.0 if (item, map_id, lab) == ("ioi", "total_zero_unfrozen", "L9H6") else 0.0

    tests = E.build_tests(fake_root(tmp_path, effect))
    t = by_id(tests)["ioi/total_zero_unfrozen/L9H6"]
    assert t["reject"] and t["z"] == 500.0 and t["p"] == 0.0
    assert t["holm_step"] <= 2  # its delta's p also underflows to 0.0; ties order by key
    assert sum(x["reject"] for x in tests) == 2  # the cell, and its frozen delta (0 - 5 = -5)
    assert by_id(tests)["ioi/delta_zero/L9H6"]["effect"] == -5.0
    conf = E.select(tests)
    assert [(s["id"], s["rank"]) for s in conf["selections"]] == [("ioi/total_zero_unfrozen/L9H6", 1)]
    assert conf["sets"]["ioi/total_zero_unfrozen"]["n_cleared"] == 1 and len(conf["sets"]) == 27
    assert "ioi/delta_zero" not in conf["sets"]  # deltas do not select


def test_mean_cells_use_the_reference_spread(tmp_path):
    spread = {0: 1.0, 1: 3.0, 2: 1.0, 3: 3.0, 4: 1.0}

    def effect(item, map_id, lab, rs):
        return spread[rs] if (item, map_id, lab) == ("induction", "total_mean_unfrozen", "L5H5") else 0.0

    tests = by_id(E.build_tests(fake_root(tmp_path, effect)))
    t = tests["induction/total_mean_unfrozen/L5H5"]
    assert t["source"] == "ref_seed_sd" and math.isclose(t["s"], statistics.stdev(spread.values()))
    assert t["effect"] == 1.0 and not t["reject"]
    d = tests["induction/delta_mean/L5H5"]  # frozen effect 0 at every seed: delta = -spread
    assert d["effect"] == -1.0 and math.isclose(d["ref_sd"], statistics.stdev(spread.values()))
    assert tests["induction/total_zero_unfrozen/L5H5"]["source"] == "sem"


def test_missing_or_incomplete_records_refuse(tmp_path):
    root = fake_root(tmp_path)
    (stage_dir(root, "floor", "agreement") / "direct_mean_s0_r3.json").unlink()
    with pytest.raises(E.SelectionError, match="missing"):
        E.build_tests(root)
    root2 = fake_root(tmp_path / "b")
    p = stage_dir(root2, "selection", "ioi") / "direct_zero_s0.json"
    rec = json.loads(p.read_text())
    rec["complete"] = False
    p.write_text(json.dumps(rec))
    with pytest.raises(E.SelectionError, match="incomplete"):
        E.build_tests(root2)


def exploratory_fixture(tmp_path):
    def effect(item, map_id, lab, rs):
        return 5.0 if (item, map_id, lab) == ("ioi", "total_zero_unfrozen", "L9H6") else 0.0

    tests = E.build_tests(fake_root(tmp_path, effect))
    return tests, E.select(tests)


def test_check_exploratory_accepts_a_well_formed_entry(tmp_path):
    tests, conf = exploratory_fixture(tmp_path)
    out = E.check_exploratory([{"item": "induction", "map": "total_zero_frozen", "component": "L5H1",
                                "why": "large frozen delta"}], conf, by_id(tests))
    assert out[0]["id"] == "induction/total_zero_frozen/L5H1" and out[0]["rank"] is None
    assert out[0]["why"] == "large frozen delta" and out[0]["effect"] == 0.0


@pytest.mark.parametrize("entry,match", [
    ({"item": "ioi", "map": "total_nope", "component": "L5H1", "why": "x"}, "unknown"),
    ({"item": "ioi", "map": "delta_zero", "component": "L5H1", "why": "x"}, "unknown"),
    ({"item": "ioi", "map": "total_zero_frozen", "component": "L12H1", "why": "x"}, "unknown"),
    ({"item": "ioi", "map": "total_zero_frozen", "component": "L5H1", "why": " "}, "why"),
    ({"item": "ioi", "map": "total_zero_frozen", "component": "L5H1"}, "exactly"),
    ({"item": "ioi", "map": "total_zero_unfrozen", "component": "L9H6", "why": "x"}, "already a confirmatory"),
])
def test_check_exploratory_refuses(tmp_path, entry, match):
    tests, conf = exploratory_fixture(tmp_path)
    with pytest.raises(E.SelectionError, match=match):
        E.check_exploratory([entry], conf, by_id(tests))


def test_check_exploratory_refuses_duplicates(tmp_path):
    tests, conf = exploratory_fixture(tmp_path)
    e = {"item": "ioi", "map": "total_zero_frozen", "component": "L5H1", "why": "x"}
    with pytest.raises(E.SelectionError, match="duplicate"):
        E.check_exploratory([e, dict(e)], conf, by_id(tests))


def test_require_committed(tmp_path):
    git = ["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(git + ["init", "-q"], check=True)
    f = tmp_path / "confirmatory.json"
    f.write_text("{}")
    with pytest.raises(E.SelectionError, match="not committed"):
        E.require_committed(f, cwd=tmp_path)
    subprocess.run(git + ["add", "confirmatory.json"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "x"], check=True)
    E.require_committed(f, cwd=tmp_path)
    f.write_text('{"edited": true}')
    with pytest.raises(E.SelectionError, match="uncommitted changes"):
        E.require_committed(f, cwd=tmp_path)
