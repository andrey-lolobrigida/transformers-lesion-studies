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
