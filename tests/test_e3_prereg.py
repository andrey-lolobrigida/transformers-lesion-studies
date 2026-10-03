"""E3 pre-registration: the constants are frozen, the counts follow from the
grid, and every inherited value agrees with the artifact it comes from.
The README mirror test is added in Task 9. Nothing here loads a model."""

import json
from pathlib import Path

import pytest

from src.lesion import e1b_gate, e1b_noise
from src.lesion import e3_prereg as P
from src.lesion.ablate import BATTERIES
from src.lesion.battery import TEMPLATE_FLOOR
from src.lesion.spec import MLP, AblationSpec, All, Head


def test_pre_registration_is_frozen():
    assert (P.N, P.SEED, P.HELD_OUT_SEED, P.REF_N) == (2000, 0, 1, 2000)
    assert P.REF_SEEDS == (0, 1, 2, 3, 4) and P.HELD_OUT_REF_SEEDS == (5, 6, 7, 8, 9)
    assert (P.BATCH_SIZE, P.VALUES, P.ALPHA, P.K) == (128, ("zero", "mean", "resample"), 0.05, 10)
    assert [(i.name, i.scheme, i.prepend_bos) for i in P.ITEMS] == [
        ("ioi", "p_ABC", False), ("induction", "fresh_prefix", True), ("agreement", "number_flip", True)]
    assert [m.id for m in P.MAPS] == [
        "total_zero_unfrozen", "total_mean_unfrozen", "total_resample_unfrozen",
        "total_zero_frozen", "total_mean_frozen", "total_resample_frozen",
        "direct_zero", "direct_mean", "direct_resample"]
    assert [(m.kind, m.value, m.frozen) for m in P.DIRECT_MAPS] == [
        ("direct", "zero", False), ("direct", "mean", False), ("direct", "resample", False)]
    assert P.FAMILIES == ("main", "verify_confirmatory", "verify_exploratory", "sufficiency_confirmatory",
                          "sufficiency_exploratory", "adversarial")
    assert P.SHUFFLE_SCHEME == "shuffle_prefix"
    assert [P.label(h) for h in P.ADV_HEADS] == ["L5H5", "L6H9", "L4H11", "L2H2"]
    assert [P.label(h) for h in P.ADV_SET] == ["L5H5", "L6H9"]
    assert P.ADV_ARMS == ("shuffle_prefix", "end_only")
    assert P.GATE2_DIR == "results/E2/I3"
    assert P.DETERMINISM_CELLS == (("ioi", "total_mean_unfrozen", "L9H6"),
                                   ("induction", "total_zero_frozen", "L5H5"),
                                   ("agreement", "direct_resample", "L0.mlp"))


def test_counts_follow_from_the_grid():
    assert len(P.COMPONENTS) == 156 == len(set(P.COMPONENTS))
    assert P.COMPONENTS[0] == Head(0, 0) and P.COMPONENTS[143] == Head(11, 11) and P.COMPONENTS[144] == MLP(0)
    assert P.N_TOTAL == len(P.ITEMS) * len(P.TOTAL_MAPS) * 156 == 2808
    assert P.N_DIRECT == len(P.ITEMS) * len(P.DIRECT_MAPS) * 156 == 1404
    assert P.N_DELTA == len(P.ITEMS) * len(P.VALUES) * 156 == 1404
    assert P.N_FAMILY == 5616


def test_inherited_constants_agree_with_their_sources():
    assert (P.GATE_ACC_MIN, P.GATE_GAP_MIN) == (e1b_gate.ACC_MIN, e1b_gate.GAP_MIN)
    assert P.GATE_TEMPLATE_FLOOR == TEMPLATE_FLOOR
    assert P.GATE1_COMPONENTS == e1b_noise.COMPONENTS
    assert P.REF_SEEDS == e1b_noise.REF_SEEDS and P.REF_N == e1b_noise.REF_N == e1b_gate.REF_N
    expected_gap = {"ioi": 3.590, "induction": 17.012, "agreement": 5.141}  # E1b gate, seed 0 (CLAUDE.md status)
    for item in P.ITEMS:
        g = json.loads(Path(item.gate_file).read_text())
        f = json.loads(Path(item.floor_file).read_text())
        assert g["verdict"]["pass"] is True and g["scheme"] == item.scheme
        assert g["battery"]["prepend_bos"] is item.prepend_bos is f["battery"]["prepend_bos"]
        assert BATTERIES[item.name].default_prepend_bos is item.prepend_bos
        assert BATTERIES[item.name].schemes[0] == item.scheme
        assert g["environment"]["batch_size"] == f["environment"]["batch_size"] == P.BATCH_SIZE
        assert (f["n"], f["seed"], f["ref_n"], f["ref_seeds"]) == (P.N, P.SEED, P.REF_N, list(P.REF_SEEDS))
        assert abs(g["statistics"]["gap"] - expected_gap[item.name]) < 5e-4
    e2 = sorted(Path(P.GATE2_DIR).glob("induction_L*.json"))
    assert len(e2) == 24
    for p in e2:
        assert json.loads(p.read_text())["environment"]["batch_size"] == P.BATCH_SIZE


def test_labels_round_trip_and_match_the_spec_labels():
    for c in P.COMPONENTS:
        assert P.parse_label(P.label(c)) == c
        spec = AblationSpec(component=c, value="zero", reference=None, component_type="node", receiver=None,
                            mlp_convention=None, positions=All(), direction="ablate-clean", freeze_patterns=False)
        assert spec.component_label() == P.label(c)
    for bad in ("L1mlp", "H3", "L1H", ""):
        with pytest.raises(ValueError):
            P.parse_label(bad)


def test_readme_mirrors_the_pre_registration():
    text = Path("results/E3/README.md").read_text()
    assert "## Pre-registration" in text
    for m in P.MAPS:
        assert f"`{m.id}`" in text, m.id
    for item in P.ITEMS:
        assert f"`{item.scheme}`" in text
    for s in ("n = 2,000", "prompt seed 0", "prompt seed 1", "reference seeds 0–4", "reference seeds 5–9",
              "α = 0.05", "k = 10", "5,616", "2,808", "1,404", "batch size 128", "`shuffle_prefix`", "`exact_zero`",
              "5.5, 6.9, 4.11, 2.2", "{5.5, 6.9}", "L9H6", "L5H5", "L0.mlp", "0.90", "1.0 logit", "≥ 30"):
        assert s in text, s
    for fam in P.FAMILIES:
        assert f"`{fam}`" in text, fam
