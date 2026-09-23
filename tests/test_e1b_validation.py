"""E1b exit checks, asserted on the artifacts written by the slow-tier CLI
runs (see results/E1b/README.md for the commands). GPU, real model, slow."""

import json
from pathlib import Path

import pytest

from src.lesion.ablate import BATTERIES
from src.lesion.e1b_gate import THRESHOLDS
from src.lesion.model import MODEL_REVISION

pytestmark = pytest.mark.slow

E0 = Path("results/E0/e0_smoke_seed0_n100000.json")
E1B = Path("results/E1b")
IDENTITY = E1B / "identity" / "ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0.json"
PAIRS = [(item, scheme) for item in ("ioi", "induction", "factual") for scheme in BATTERIES[item].schemes]


def load(path: Path) -> dict:
    if not path.exists():
        pytest.fail(f"{path} missing: see results/E1b/README.md for the command")
    return json.loads(path.read_text())


def gate(item: str, scheme: str) -> dict:
    return load(E1B / "gate" / item / f"{scheme}.json")


def test_identity_against_e0_after_the_protocol_change():
    """The E1a identity check, re-run on the E1b code: the clean pass still equals E0's, bitwise."""
    e0 = load(E0)["ioi"]["no_bos"]
    d = load(IDENTITY)
    clean = d["results"]["clean"]
    assert clean["n"] == e0["n"] == 100000
    assert clean["mean_ld"] == e0["mean_logit_diff"]
    assert clean["std_ld"] == e0["std_logit_diff"]
    assert clean["sem_ld"] == e0["sem_logit_diff"]
    assert clean["c_over_s"] == e0["io_over_s_fraction"]
    assert clean["mean_p_c"] == e0["mean_io_prob"]
    for t, v in e0["by_template"].items():
        assert d["results"]["by_template"][t]["clean"]["mean_ld"] == v["mean_logit_diff"], t
    assert d["battery"]["corruption"]["name"] == "p_ABC" and d["cli"]["corruption"] == "p_ABC"


@pytest.mark.parametrize("item,scheme", PAIRS)
def test_gate_artifact(item, scheme):
    d = gate(item, scheme)
    gated = scheme == BATTERIES[item].schemes[0]
    assert d["gated"] is gated and d["thresholds"] == THRESHOLDS
    assert d["battery"]["expected_direction"] == "positive" and d["battery"]["corruption"]["name"] == scheme
    assert d["environment"]["model"]["revision"] == MODEL_REVISION and d["command"].startswith("uv run python -m")
    if gated:
        conds = set(d["verdict"]["conditions"])
        assert conds == ({"pairwise_accuracy", "gap", "survivors"} if item == "factual" else {"pairwise_accuracy", "gap"})
        assert d["verdict"]["pass"] == all(c["pass"] for c in d["verdict"]["conditions"].values())
        assert d["pre_registered"] is True
    else:
        assert d["verdict"] is None
    if item != "factual":
        assert d["battery"]["n"] == 2000 and d["reference_floor"]["ref_n"] == 1000
    assert d["battery"]["prepend_bos"] is (item == "induction")


def test_factual_gate_reads_the_survivor_file():
    survivors = json.loads(Path("batteries/factual/survivors.json").read_text())["counts"]["admitted"]
    d = gate("factual", "subject_swap")
    assert d["verdict"]["conditions"]["survivors"]["value"] == survivors == d["battery"]["n"]
