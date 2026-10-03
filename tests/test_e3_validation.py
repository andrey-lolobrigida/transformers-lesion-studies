"""E3 exit checks, asserted on the committed artifacts of Tasks 10-14
(see results/E3/README.md for the commands). GPU runs must exist; slow."""

import json
from pathlib import Path

import pytest

from src.lesion.e1b_gate import THRESHOLDS
from src.lesion.model import MODEL_REVISION

pytestmark = pytest.mark.slow

E3 = Path("results/E3")


def load(path: Path) -> dict:
    if not path.exists():
        pytest.fail(f"{path} missing: see results/E3/README.md for the command")
    return json.loads(path.read_text())


def test_validation_gates_passed():
    expected = {"e1b_identity": 432, "e2_identity": 96, "determinism": 3}
    for gate, compared in expected.items():
        d = load(E3 / "gates" / f"{gate}.json")
        assert d["pass"] is True and d["compared"] == compared, gate
        assert d["environment"]["model"]["revision"] == MODEL_REVISION


def test_shuffle_prefix_gate_artifact():
    d = load(E3 / "gates" / "induction" / "shuffle_prefix.json")
    fresh = load(Path("results/E1b/gate/induction/fresh_prefix.json"))
    assert d["thresholds"] == THRESHOLDS and d["pre_registered"] is True and d["verdict"] is not None
    assert d["battery"]["n"] == 2000 and d["battery"]["prepend_bos"] is True
    assert d["battery"]["corruption"]["name"] == "shuffle_prefix"
    assert d["statistics"]["pairwise_accuracy"] == fresh["statistics"]["pairwise_accuracy"]  # shared clean stream
    assert d["statistics"]["clean"]["mean_ld"] == fresh["statistics"]["clean"]["mean_ld"]


def test_sweep_and_floor_are_complete_and_consistent():
    from src.lesion.e3_prereg import COMPONENTS, ITEM, MAP, label
    from src.lesion.e3_sweep import cell_sets, cell_spec, stage_dir

    for stage, expected in (("selection", 27), ("floor", 36)):
        sets = cell_sets(tuple(ITEM), stage)
        assert len(sets) == expected
        for cs in sets:
            rec = load(stage_dir(E3, stage, cs.item) / f"{cs.stem}.json")
            assert rec["complete"] and rec["pre_registered"], cs
            assert rec["components"] == [label(c) for c in COMPONENTS]
            for c in COMPONENTS:
                assert rec["cells"][label(c)]["spec"] == cell_spec(c, MAP[cs.map_id], cs.ref_seed).to_json()
            assert (stage_dir(E3, stage, cs.item) / f"{cs.stem}.parquet").exists() == (stage == "selection")
    for item in ITEM:
        assert (E3 / "sweep" / item / "clean_s0.parquet").exists()


def test_selection_is_reproducible_from_the_family():
    from src.lesion.e3_select import select

    tests = load(E3 / "selection" / "tests.json")
    conf = load(E3 / "selection" / "confirmatory.json")
    assert tests["n_tests"] == len(tests["tests"]) == 5616
    again = select(tests["tests"])
    assert again["selections"] == conf["selections"] and again["sets"] == conf["sets"]
