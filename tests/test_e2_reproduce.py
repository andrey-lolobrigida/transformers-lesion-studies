"""E2 driver: the pre-registration is frozen, the verdict rules behave per
branch, verdicts are withheld off the pre-registered settings, the README
mirrors the constants. Nothing here loads a model."""

import json
from pathlib import Path

import pytest

from src.lesion import e2_reproduce as R
from src.lesion.induction import LABELS as INDUCTION_LABELS
from src.lesion.ioi import LABELS as IOI_LABELS
from src.lesion.spec import Head, Logits, SpecError


def wang(hs):
    return " ".join(f"{h.layer}.{h.head}" for h in hs)


def test_pre_registration_is_frozen():
    assert (R.N, R.SEED, R.REF_N, R.REF_SEED) == (2000, 0, 2000, 0)
    assert R.VALUES == ("zero", "mean", "resample")
    assert (R.IOI_BOS, R.INDUCTION_BOS, R.I1_BOS) == (False, True, False)
    assert (R.I1_N_SEQ, R.I1_HALF_LEN, R.I1_SPREAD_SEEDS) == (100, 100, (1, 2, 3, 4))
    assert {c.name: (wang(c.members), c.position) for c in R.CLASSES} == {
        "name_mover": ("9.6 9.9 10.0", "END"),
        "negative_name_mover": ("10.7 11.10", "END"),
        "s_inhibition": ("7.3 7.9 8.6 8.10", "END"),
        "induction": ("5.5 5.8 5.9 6.9", "S2"),
        "duplicate_token": ("0.1 0.10 3.0", "S2"),
        "previous_token": ("2.2 4.11", "S1+1"),
        "backup_name_mover": ("9.0 9.7 10.1 10.2 10.6 10.10 11.2 11.9", "END"),
    }
    assert [(r.id, r.score, wang(r.members), r.k, r.bottom) for r in R.I1_ROWS] == [
        ("I1/previous_token", "previous_token", "4.11 2.2", 4, False),
        ("I1/induction", "induction", "5.5 6.9", 5, False),
        ("I1/duplicate", "duplicate", "3.0 0.1", 4, False),
        ("I1/copy", "copy_abs", "5.5 6.9", 20, False),
    ]
    assert (wang(R.I2_SENDERS), wang(R.I2_RECEIVERS)) == ("4.11 2.2", "5.5 6.9")
    assert [(r.name, r.sender_position, r.receiver.targets, r.expected) for r in R.I2_ROUTES] == [
        ("k_route", "S1+1", ((5, 5, "k", "S1+1"), (6, 9, "k", "S1+1")), "positive"),
        ("q_route", "S2", ((5, 5, "q", "S2"), (6, 9, "q", "S2")), "null"),
    ]
    assert (R.I2_BASELINE_DRAWS, R.I2_BASELINE_SEED) == (200, 0)
    assert (wang(R.I3_HEADS), wang(R.I3_SET)) == ("5.5 6.9 4.11 2.2", "5.5 6.9")
    assert [(wang((h,)), p) for h, p in R.I4_MEMBERS] == [("5.5", "END"), ("6.9", "END"), ("4.11", "B1"), ("2.2", "B1")]
    assert [(s.name, s.sender_position, len(s.candidates)) for s in R.P1_SWEEPS] == [
        ("logits", "END", 144), ("nm_queries", "END", 108), ("sinh_values", "S2", 84), ("ind_keys", "S1+1", 60)]
    assert R.P1_SWEEPS[1].receiver.targets == ((9, 6, "q", "END"), (9, 9, "q", "END"), (10, 0, "q", "END"))
    assert R.P1_SWEEPS[2].receiver.targets == ((7, 3, "v", "S2"), (7, 9, "v", "S2"), (8, 6, "v", "S2"), (8, 10, "v", "S2"))
    assert R.P1_SWEEPS[3].receiver.targets == ((5, 5, "k", "S1+1"), (6, 9, "k", "S1+1"))
    assert [(r.id, r.score, wang(r.members), r.k, r.bottom) for r in R.P1_ROWS] == [
        ("P1/name_mover", "logits", "9.6 9.9 10.0", 5, False),
        ("P1/negative_name_mover", "logits", "10.7 11.10", 4, True),
        ("P1/s_inhibition", "nm_queries", "7.3 7.9 8.6 8.10", 6, False),
        ("P1/induction_duplicate", "sinh_values", "5.5 6.9 3.0 0.1", 6, False),
        ("P1/previous_token", "ind_keys", "4.11 2.2", 4, False),
    ]
    assert [(i, s, wang(m), e) for i, s, m, e in R.P1_SIGN] == [
        ("P1/name_mover/sign", "logits", "9.6 9.9 10.0", "positive"),
        ("P1/negative_name_mover/sign", "logits", "10.7 11.10", "negative"),
    ]
    assert wang(R.P1_FUZZY) == "0.10 5.8 5.9"
    assert [c.id for c in R.CORNERS] == ["t15-ref210", "t15-ref2000", "t7-ref98", "t7-ref2000"]
    assert (R.P2_PUBLISHED, R.P3_PUBLISHED, R.P3_PUBLISHED_ABS_GAP, R.P3_CONTRAST) == (0.05, 0.87, 0.46, 1.0)
    assert R.FLOOR_FILES == {"ioi": "results/E1b/noise/ioi/floor.json"}


def test_the_circuit_is_wangs_26_heads_at_ioi_positions():
    circuit = [h for c in R.CLASSES for h in c.members]
    assert len(circuit) == len(set(circuit)) == 26
    assert all(c.position in IOI_LABELS for c in R.CLASSES)
    assert all(p in INDUCTION_LABELS for _, p in R.I4_MEMBERS)


def test_every_path_is_nonempty_by_construction():
    for s in R.P1_SWEEPS:
        R.check_direct_path(s.sender_position, s.receiver)
    for r in R.I2_ROUTES:
        R.check_direct_path(r.sender_position, r.receiver)
    with pytest.raises(SpecError):
        R.check_direct_path("S1+1", R.I2_ROUTES[1].receiver)  # q at S2: the path would be empty
    with pytest.raises(SpecError):
        R.check_direct_path("S2", Logits())


def test_published_members_are_candidates():
    sweeps = {s.name: s for s in R.P1_SWEEPS}
    for row in R.P1_ROWS:
        assert set(row.members) <= set(sweeps[row.score].candidates), row.id
    assert set(R.P1_FUZZY) <= set(sweeps["sinh_values"].candidates)
    for s in R.P1_SWEEPS[1:]:
        assert all(h.layer < min(t[0] for t in s.receiver.targets) for h in s.candidates)


def test_helpers():
    assert R.head("10.10") == Head(10, 10) and R.label(Head(9, 6)) == "L9H6"
    assert len(R.ALL_HEADS) == 144
    assert R.Corner(7, 98).id == "t7-ref98"


S = {"a": 5.0, "b": 4.0, "c": 3.0, "d": 3.0, "e": 1.0, "f": -2.0}


def test_identity_matched_and_not():
    assert R.identity_verdict(S, ("a", "b"), 2, False)["verdict"] == R.MATCHED
    assert R.identity_verdict(S, ("a", "e"), 3, False)["verdict"] == R.NOT_MATCHED


def test_identity_tie_straddling_the_cut_counts_inside():
    v = R.identity_verdict(S, ("d",), 3, False)
    assert v["member_ranks"] == {"d": 3} and v["verdict"] == R.MATCHED and v["tie_at_cut"] is True
    assert R.identity_verdict(S, ("a",), 2, False)["tie_at_cut"] is False


def test_identity_from_the_bottom():
    v = R.identity_verdict(S, ("f", "e"), 2, True)
    assert v["member_ranks"] == {"f": 1, "e": 2} and v["verdict"] == R.MATCHED
    assert R.identity_verdict(S, ("f", "a"), 4, True)["verdict"] == R.NOT_MATCHED


def test_identity_refuses_missing_members_and_nonfinite_scores():
    with pytest.raises(ValueError, match="not among"):
        R.identity_verdict(S, ("zz",), 2, False)
    with pytest.raises(ValueError, match="non-finite"):
        R.identity_verdict({**S, "g": float("nan")}, ("a",), 2, False)


def test_sign_rule_branches():
    assert R.sign_verdict(0.5, 0.01, 0.04, "positive")["verdict"] == R.MATCHED
    assert R.sign_verdict(-0.5, 0.01, 0.04, "positive")["verdict"] == R.NOT_MATCHED  # wrong sign
    assert R.sign_verdict(0.03, 0.001, 0.04, "positive")["verdict"] == R.NOT_MATCHED  # inside the floor
    v = R.sign_verdict(0.07, 0.05, 0.04, "positive")
    assert v["bound"] == 0.1 and v["bound_source"] == "2*sem" and v["verdict"] == R.NOT_MATCHED
    assert R.sign_verdict(-0.5, 0.01, 0.04, "negative")["verdict"] == R.MATCHED
    assert R.sign_verdict(0.02, 0.01, 0.04, "null")["verdict"] == R.MATCHED
    assert R.sign_verdict(-0.2, 0.01, 0.04, "null")["verdict"] == R.NOT_MATCHED
    with pytest.raises(ValueError):
        R.sign_verdict(0.0, 0.0, 0.0, "up")


def test_magnitude_rule_branches():
    four = {"a": 0.80, "b": 0.85, "c": 0.90, "d": 0.88}
    assert R.magnitude_verdict(four, 0.87, 1.0)["verdict"] == R.MATCHED
    assert R.magnitude_verdict(four, 0.95, 1.0)["verdict"] == R.NOT_MATCHED
    # the contrast inside wins, even with the published value inside too
    assert R.magnitude_verdict({**four, "d": 1.02}, 0.87, 1.0)["verdict"] == R.UNINFORMATIVE
    v = R.magnitude_verdict({"a": 0.03, "b": 0.06}, 0.05, {"a": 0.20, "b": 0.07})
    assert v["verdict"] == R.MATCHED and v["contrast_range"] == [0.07, 0.20]
    assert R.magnitude_verdict({"a": 0.03, "b": 0.08}, 0.05, {"a": 0.20, "b": 0.07})["verdict"] == R.UNINFORMATIVE
    assert R.magnitude_verdict(four, 0.87, 1.0)["width"] == pytest.approx(0.10)


def test_sign_and_magnitude_refuse_nonfinite_inputs():
    nan = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        R.sign_verdict(nan, 0.01, 0.04, "positive")
    with pytest.raises(ValueError, match="non-finite"):
        R.sign_verdict(0.5, nan, 0.04, "positive")
    with pytest.raises(ValueError, match="non-finite"):
        R.sign_verdict(0.5, 0.01, nan, "positive")
    four = {"a": 0.80, "b": 0.85, "c": 0.90, "d": 0.88}
    with pytest.raises(ValueError, match="non-finite"):
        R.magnitude_verdict({**four, "d": nan}, 0.87, 1.0)
    with pytest.raises(ValueError, match="non-finite"):
        R.magnitude_verdict(four, nan, 1.0)
    with pytest.raises(ValueError, match="non-finite"):
        R.magnitude_verdict(four, 0.87, nan)
    with pytest.raises(ValueError, match="non-finite"):
        R.magnitude_verdict(four, 0.87, {"a": 0.20, "b": nan})


def test_verdicts_are_withheld_off_pre_registration(tmp_path):
    e = R.entry("I2/x", "src", 1.0, 2.0, "tol", {"rule": "sign", "verdict": R.MATCHED})
    d = json.loads(R.write_verdicts(tmp_path, "I2", [e], pre_registered=False).read_text())
    assert d["pre_registered"] is False and d["entries"][0]["verdict"] is None
    assert "withheld" in d["entries"][0] and e["verdict"] == R.MATCHED  # the caller's entry is not mutated
    d = json.loads(R.write_verdicts(tmp_path, "I2", [e], pre_registered=True).read_text())
    assert d["entries"][0]["verdict"] == R.MATCHED
    assert R.is_pre_registered(2000, 0) and not R.is_pre_registered(64, 0) and not R.is_pre_registered(2000, 1)


def test_exit_table(tmp_path):
    R.write_verdicts(tmp_path, "I1", [R.entry("I1/a", "s", "p", "o", "t", {"verdict": R.MATCHED})], True)
    R.write_verdicts(tmp_path, "P3", [R.entry("P3/b", "s", 0.87, [0.8, 1.0], "t", {"verdict": R.UNINFORMATIVE})], True)
    t = R.build_table(tmp_path)
    assert [r["id"] for r in t["rows"]] == ["I1/a", "P3/b"]
    assert t["counts"] == {R.MATCHED: 1, R.UNINFORMATIVE: 1}
    assert t["missing"] == ["I2", "I3", "I4", "P1", "P2", "P4"]
    assert json.loads((tmp_path / "verdicts.json").read_text()) == t


def test_floor_is_read_from_the_committed_e1b_artifact():
    d = json.loads(Path("results/E1b/noise/ioi/floor.json").read_text())
    assert R.floor_for("ioi") == d["max_floor"] and d["ref_n"] == 2000 and d["ref_seeds"] == [0, 1, 2, 3, 4]


def test_cli_refuses_before_the_model_loads(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise AssertionError("model loaded")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    with pytest.raises(SystemExit) as e:
        R.main(["--target", "I1", "--n", "0"])
    assert e.value.code == 2
    with pytest.raises(SystemExit):
        R.main(["--target", "nope"])
    assert R.main(["--target", "table", "--out-dir", str(tmp_path)]) == 0


def test_readme_mirrors_the_pre_registration():
    text = Path("results/E2/README.md").read_text()
    assert "## Pre-registration" in text
    for row in (*R.I1_ROWS, *R.P1_ROWS):
        assert f"`{row.id}`" in text and f"k = {row.k}" in text, row.id
    for c in R.CLASSES:
        assert f"`{c.name}`" in text
    for c in R.CORNERS:
        assert f"`{c.id}`" in text
    for x in ("0.05", "0.87", "0.46", "`k_route`", "`q_route`"):
        assert x in text
