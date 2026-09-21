"""E1a exit checks, asserted on the artifacts written by
``uv run python -m src.lesion.e1a_validate``. GPU, real model, slow."""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

pytestmark = pytest.mark.slow

E0 = Path("results/E0/e0_smoke_seed0_n100000.json")
E1A = Path("results/E1a")
IDENTITY = E1A / "ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0.json"
MLP0_MEAN = "ioi_L0mlp_mean-corrupt-n1000-s0-template_node_all_ablate-clean_n2000_seed0"


def load(path: Path) -> dict:
    if not path.exists():
        pytest.fail(f"{path} missing: run `uv run python -m src.lesion.e1a_validate` first")
    return json.loads(path.read_text())


def test_identity_against_e0():
    """Check 1: the harness's clean pass equals E0's on every shared field, bitwise."""
    e0 = load(E0)["ioi"]["no_bos"]
    clean = load(IDENTITY)["results"]["clean"]
    assert clean["n"] == e0["n"] == 100000
    assert clean["mean_ld"] == e0["mean_logit_diff"]
    assert clean["std_ld"] == e0["std_logit_diff"]
    assert clean["sem_ld"] == e0["sem_logit_diff"]
    assert clean["c_over_s"] == e0["io_over_s_fraction"]
    assert clean["mean_p_c"] == e0["mean_io_prob"]
    by_t = load(IDENTITY)["results"]["by_template"]
    assert set(by_t) == set(e0["by_template"]) and len(by_t) == 30
    for t, v in e0["by_template"].items():
        assert by_t[t]["n"] == v["n"]
        assert by_t[t]["clean"]["mean_ld"] == v["mean_logit_diff"], t
    env = load(IDENTITY)["environment"]
    assert env["batch_size"] == 512 and env["model"]["revision"] == load(E0)["model"]["revision"]


@pytest.mark.parametrize("layer", range(12))
@pytest.mark.parametrize("value", ["zero", "mean-corrupt-n1000-s0-template", "resample"])
def test_mlp_table_artifacts(layer, value):
    """Check 2's inputs exist, with the reference size logged next to every mean number."""
    d = load(E1A / f"ioi_L{layer}mlp_{value}_node_all_ablate-clean_n2000_seed0.json")
    assert d["spec"]["component"] == {"kind": "mlp", "layer": layer}
    assert d["spec"]["freeze_patterns"] is False and d["direct_effect_definition"] is None
    assert d["battery"]["n"] == 2000 and d["battery"]["corruption"]["name"] == "p_ABC"
    if value.startswith("mean"):
        assert d["spec"]["reference"] == {"battery_side": "corrupt", "n": 1000, "seed": 0, "match": "template"}
        assert d["reference"]["n"] == 1000 and len(d["reference"]["per_template_counts"]) == 30
        assert min(d["reference"]["per_template_counts"].values()) >= 1
    else:
        assert d["reference"] is None
    assert "effect_mean" in d["results"]["effect"]["ld"] and "sem" in d["results"]["effect"]["ld"]


def test_mlp0_sign_is_recorded_not_asserted():
    """The bracket claim (Wang App. J: mean-ablating MLP0 on p_ABC flips the sign) is
    stated in the README whichever way it falls (D-011). This test only pins that the
    number the README cites is the one in the artifact."""
    d = load(E1A / f"{MLP0_MEAN}.json")
    readme = (E1A / "README.md").read_text()
    assert f"{d['results']['ablated']['mean_ld']:+.3f}" in readme


def test_determinism_rerun_identical():
    """Check 3: two invocations differ only in environment.seconds."""
    a = load(E1A / f"{MLP0_MEAN}.json")
    b = load(E1A / "rerun" / f"{MLP0_MEAN}.json")
    for d in (a, b):
        d["environment"].pop("seconds")
        d["cli"].pop("out_dir")
        d["command"] = d["command"].replace("results/E1a/rerun", "results/E1a")
    assert a == b
    assert pq.read_table(E1A / f"{MLP0_MEAN}.parquet").equals(pq.read_table(E1A / "rerun" / f"{MLP0_MEAN}.parquet"))
