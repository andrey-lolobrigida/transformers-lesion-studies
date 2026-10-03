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
# The schemes E1b gated. shuffle_prefix (E3, D-016 item 6) is gated by e3_verify into results/E3/gates/.
E1B_SCHEMES = {"ioi": BATTERIES["ioi"].schemes, "induction": ("fresh_prefix",),
               "factual": BATTERIES["factual"].schemes, "agreement": BATTERIES["agreement"].schemes}
PAIRS = [(item, scheme) for item in ("ioi", "induction", "factual", "agreement") for scheme in E1B_SCHEMES[item]]


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
        assert d["battery"]["n"] == 2000 and d["reference_floor"]["ref_n"] == 2000
        assert d["reference_floor"]["templates_below_floor"] == []  # O-015: ref n chosen to meet the floor
    assert d["battery"]["prepend_bos"] is BATTERIES[item].default_prepend_bos


def test_factual_gate_reads_the_survivor_file():
    survivors = json.loads(Path("batteries/factual/survivors.json").read_text())["counts"]["admitted"]
    d = gate("factual", "subject_swap")
    assert d["verdict"]["conditions"]["survivors"]["value"] == survivors == d["battery"]["n"]


@pytest.mark.parametrize("item", ["ioi", "induction", "factual", "agreement"])
def test_noise_floor(item):
    default = BATTERIES[item].schemes[0]
    if not gate(item, default)["verdict"]["pass"]:
        assert not (E1B / "noise" / item / "floor.json").exists(), "a floor was measured for an item that failed"
        return
    d = load(E1B / "noise" / item / "floor.json")
    assert d["scheme"] == default and d["ref_seeds"] == [0, 1, 2, 3, 4] and d["seed"] == 0
    assert len(d["rows"]) == 24 and all(len(r["effect_mean_by_ref_seed"]) == 5 for r in d["rows"])
    assert d["spec_template"]["reference"]["n"] == d["ref_n"] and d["spec_template"]["reference"]["match"] == "template"
    assert d["max_floor"] == max(r["floor"] for r in d["rows"])
    if item != "factual":
        assert (d["n"], d["ref_n"]) == (2000, 2000)


@pytest.mark.parametrize("item", ["ioi", "induction", "factual", "agreement"])
def test_readme_cites_the_gate_numbers(item):
    d = gate(item, BATTERIES[item].schemes[0])
    readme = (E1B / "README.md").read_text()
    if d["statistics"] is not None:
        assert f"{d['statistics']['pairwise_accuracy']:.3f}" in readme
        assert f"{d['statistics']['gap']:+.3f}" in readme


def test_agreement_gate_breakdown_and_labelling():
    for scheme in BATTERIES["agreement"].schemes:
        d = gate("agreement", scheme)
        assert d["battery"]["corruption"]["source"] == "ours (D-013 fallback; unsourced)"
        b = d["breakdown"]
        assert set(b) == {"congruency", "verb", "subject_number"}
        assert set(b["congruency"]) == {"congruent", "incongruent"} and set(b["verb"]) == {"is/are", "has/have"}
        assert sum(r["n"] for r in b["congruency"].values()) == d["statistics"]["n"] == 2000
        assert len(d["reference_floor"]["per_template_counts"]) == 8
