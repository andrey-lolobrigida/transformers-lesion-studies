"""Subject-verb agreement pairs (D-013 fallback, unsourced; agreement addendum 2026-09-24)."""

from collections import Counter
from types import SimpleNamespace

import pytest

from src.lesion.agreement import (
    LABELS, NOUNS, NUMBER_FLIP, NUMBER_FLIP_ALL, PREPS, VERBS, AgreementBattery, kept_nouns,
)
from src.lesion.battery import AlignmentError
from tests.conftest import WordTokenizer


class SplittingTokenizer(WordTokenizer):
    """WordTokenizer, except that each word in ``split`` (with its leading
    space, as the generator encodes it) comes out as two tokens."""

    def __init__(self, split) -> None:
        super().__init__()
        self.split = set(split)

    def __call__(self, text: str, add_special_tokens: bool = False):
        if text.strip() in self.split:
            a = self.vocab.setdefault(text, len(self.vocab) + 1)
            b = self.vocab.setdefault("##" + text, len(self.vocab) + 1)
            return SimpleNamespace(input_ids=[a, b])
        return super().__call__(text, add_special_tokens)


def test_constants_and_fields(word_tokenizer):
    b = AgreementBattery(word_tokenizer)
    assert len(NOUNS) == 50 and len(set(NOUNS)) == 50
    assert all(not w.endswith("s") for w in NOUNS)
    assert PREPS == ("near", "behind", "beside", "with")
    assert VERBS == (("is", "are"), ("has", "have"))
    assert b.labels == LABELS == ("N1", "PREP", "N2", "END")
    assert b.schemes == ("number_flip", "number_flip_all") and b.corruption is NUMBER_FLIP
    assert AgreementBattery(word_tokenizer, "number_flip_all").corruption is NUMBER_FLIP_ALL
    assert b.expected_direction == "positive" and b.default_prepend_bos is True
    assert b.breakdown_keys == ("congruency", "verb", "subject_number")
    for c in (NUMBER_FLIP, NUMBER_FLIP_ALL):
        assert c.source == "ours (D-013 fallback; unsourced)"
    assert "unsourced" in b.template_set and "no published number" in b.template_set
    with pytest.raises(ValueError):
        AgreementBattery(word_tokenizer, "nope")


def test_filter_drops_multi_token_nouns_whole():
    tok = SplittingTokenizer({"owls", "eagle"})  # a plural in one case, a singular in the other
    kept = [w for w, _, _ in kept_nouns(tok)]
    assert "owl" not in kept and "eagle" not in kept
    assert len(kept) == len(NOUNS) - 2
    b = AgreementBattery(tok)
    words = {p.meta["n1"] for p in b.pairs(2000, 0, False)} | {p.meta["n2"] for p in b.pairs(2000, 0, False)}
    assert not words & {"owl", "owls", "eagle", "eagles"}


@pytest.mark.parametrize("word", ["are", "has", "beside", "the", "The"])
def test_multi_token_fixed_word_is_a_hard_stop(word):
    with pytest.raises(AlignmentError):
        AgreementBattery(SplittingTokenizer({word}))


def test_pairs_are_well_formed(word_tokenizer):
    b = AgreementBattery(word_tokenizer)
    ids = {w: {"sg": s, "pl": p} for w, s, p in b.nouns}
    one = lambda w: word_tokenizer(" " + w).input_ids[0]  # noqa: E731
    the_start = word_tokenizer("The").input_ids[0]
    for pr in b.pairs(1000, seed=0, prepend_bos=False):
        m = pr.meta
        assert m["n1"] != m["n2"]
        assert len(pr.clean_ids) == len(pr.corrupt_ids) == 5
        assert pr.positions == pr.corrupt_positions == {"N1": 1, "PREP": 2, "N2": 4, "END": 4}
        n1 = ids[m["n1"]]["pl" if m["subject_number"] == "plural" else "sg"]
        congruent = m["congruency"] == "congruent"
        n2_plural = (m["subject_number"] == "plural") == congruent
        n2 = ids[m["n2"]]["pl" if n2_plural else "sg"]
        assert pr.clean_ids == (the_start, n1, one(m["prep"]), one("the"), n2)
        assert pr.template == f"{m['prep']}/{m['congruency']}"
        sg, pl = m["verb"].split("/")
        assert (sg, pl) in VERBS
        c, s = (one(pl), one(sg)) if m["subject_number"] == "plural" else (one(sg), one(pl))
        assert (pr.answer_id, pr.competitor_id) == (c, s)
        assert c not in pr.clean_ids + pr.corrupt_ids and s not in pr.clean_ids + pr.corrupt_ids


def test_number_flip_changes_only_n1(word_tokenizer):
    b = AgreementBattery(word_tokenizer)
    ids = {w: (s, p) for w, s, p in b.nouns}
    for pr in b.pairs(500, seed=1, prepend_bos=False):
        diff = [k for k in range(5) if pr.clean_ids[k] != pr.corrupt_ids[k]]
        assert diff == [1]
        sg, pl = ids[pr.meta["n1"]]
        assert {pr.clean_ids[1], pr.corrupt_ids[1]} == {sg, pl}


def test_number_flip_all_changes_both_nouns(word_tokenizer):
    b = AgreementBattery(word_tokenizer, "number_flip_all")
    ids = {w: (s, p) for w, s, p in b.nouns}
    for pr in b.pairs(500, seed=1, prepend_bos=False):
        diff = [k for k in range(5) if pr.clean_ids[k] != pr.corrupt_ids[k]]
        assert diff == [1, 4]
        assert {pr.clean_ids[1], pr.corrupt_ids[1]} == set(ids[pr.meta["n1"]])
        assert {pr.clean_ids[4], pr.corrupt_ids[4]} == set(ids[pr.meta["n2"]])


def test_clean_stream_is_scheme_independent(word_tokenizer):
    a = AgreementBattery(word_tokenizer, "number_flip").pairs(300, seed=5, prepend_bos=True)
    b = AgreementBattery(word_tokenizer, "number_flip_all").pairs(300, seed=5, prepend_bos=True)
    for x, y in zip(a, b):
        assert (x.clean_ids, x.answer_id, x.competitor_id, x.template, x.meta) == \
               (y.clean_ids, y.answer_id, y.competitor_id, y.template, y.meta)


def test_draws_are_balanced(word_tokenizer):
    pairs = AgreementBattery(word_tokenizer).pairs(4000, seed=0, prepend_bos=False)
    templates = Counter(p.template for p in pairs)
    assert set(templates) == {f"{p}/{c}" for p in PREPS for c in ("congruent", "incongruent")}
    assert all(400 <= k <= 600 for k in templates.values())  # 500 expected each
    for key in ("congruency", "subject_number", "verb"):
        counts = Counter(p.meta[key] for p in pairs)
        assert len(counts) == 2 and all(1850 <= k <= 2150 for k in counts.values()), key


def test_seeded(word_tokenizer):
    b = AgreementBattery(word_tokenizer)
    assert b.pairs(50, 3, False) == b.pairs(50, 3, False) != b.pairs(50, 4, False)


def test_generator_emits_no_bos_and_bos_shifts_labels(word_tokenizer):
    b = AgreementBattery(word_tokenizer)
    bos = word_tokenizer.bos_token_id
    for a, w in zip(b.pairs(50, 1, False), b.pairs(50, 1, True)):
        assert bos not in a.clean_ids and bos not in a.corrupt_ids
        assert w.clean_ids == (bos, *a.clean_ids) and w.corrupt_ids == (bos, *a.corrupt_ids)
        assert w.positions == {k: v + 1 for k, v in a.positions.items()} == w.corrupt_positions


@pytest.mark.slow
def test_real_tokenizer_keeps_46_nouns_and_aligns():
    from src.lesion.battery import encode
    from src.lesion.model import plain_tokenizer

    tok = plain_tokenizer()
    b = AgreementBattery(tok)
    kept = {w for w, _, _ in b.nouns}
    assert len(kept) == 46 and set(NOUNS) - kept == {"owl", "eagle", "baker", "painter"}
    for pr in b.pairs(200, seed=0, prepend_bos=False):
        m = pr.meta
        n1 = m["n1"] + ("s" if m["subject_number"] == "plural" else "")
        n2_plural = (m["subject_number"] == "plural") == (m["congruency"] == "congruent")
        n2 = m["n2"] + ("s" if n2_plural else "")
        assert tuple(encode(tok, f"The {n1} {m['prep']} the {n2}")) == pr.clean_ids  # whole-string tokenisation agrees
