"""Induction pairs [olsson-2022 §Data Collection (3)], with the spec's stated departures."""

import hashlib

import pytest

from src.lesion.induction import FRESH_PREFIX, HI, I_MAX, LABELS, LO, SEQ, SHUFFLE_PREFIX, InductionBattery


def test_constants_and_fields(word_tokenizer):
    b = InductionBattery(word_tokenizer)
    assert (LO, HI, SEQ, I_MAX) == (1000, 45000, 25, 22)
    assert b.labels == LABELS == ("A1", "B1", "S_POS", "END")
    assert b.schemes == ("fresh_prefix", "shuffle_prefix") and b.corruption is FRESH_PREFIX
    assert b.expected_direction == "positive" and b.default_prepend_bos is True
    with pytest.raises(ValueError):
        InductionBattery(word_tokenizer, "nope")


def test_pairs_are_well_formed(word_tokenizer):
    pairs = InductionBattery(word_tokenizer).pairs(500, seed=0, prepend_bos=False)
    seen_i = set()
    for pr in pairs:
        i, j = int(pr.meta["i"]), int(pr.meta["j"])
        seen_i.add(i)
        assert 1 <= i <= I_MAX and i + 3 <= j <= SEQ
        xs, ys = pr.clean_ids[:SEQ], pr.corrupt_ids[:SEQ]
        assert len(pr.clean_ids) == len(pr.corrupt_ids) == SEQ + i
        assert len(set(xs)) == SEQ and len(set(ys)) == SEQ and not (set(xs) & set(ys))
        assert all(LO <= t < HI for t in xs + ys)
        assert pr.clean_ids[SEQ:] == pr.corrupt_ids[SEQ:] == xs[:i]  # second half identical
        p = pr.positions
        assert p == pr.corrupt_positions
        assert p == {"A1": i - 1, "B1": i, "S_POS": j - 1, "END": SEQ + i - 1}
        assert pr.clean_ids[p["END"]] == pr.clean_ids[p["A1"]] == xs[i - 1]
        assert pr.answer_id == xs[i] == pr.clean_ids[p["B1"]]
        assert pr.competitor_id == xs[j - 1] == pr.clean_ids[p["S_POS"]]
        assert pr.answer_id not in pr.corrupt_ids and pr.competitor_id not in pr.corrupt_ids
        assert pr.template == f"i{i}"
    assert seen_i == set(range(1, I_MAX + 1))


def test_seeded_and_clean_stream_independent_of_corruption(word_tokenizer):
    b = InductionBattery(word_tokenizer)
    a1, a2 = b.pairs(20, seed=3, prepend_bos=False), b.pairs(20, seed=3, prepend_bos=False)
    assert a1 == a2 and a1 != b.pairs(20, seed=4, prepend_bos=False)


def test_generator_emits_no_bos_and_bos_shifts_labels(word_tokenizer):
    b = InductionBattery(word_tokenizer)
    bos = word_tokenizer.bos_token_id
    plain, with_ = b.pairs(50, seed=1, prepend_bos=False), b.pairs(50, seed=1, prepend_bos=True)
    for a, w in zip(plain, with_):
        assert bos not in a.clean_ids and bos not in a.corrupt_ids
        assert w.clean_ids == (bos, *a.clean_ids) and w.corrupt_ids == (bos, *a.corrupt_ids)
        assert w.clean_ids.count(bos) == 1
        assert w.positions == {k: v + 1 for k, v in a.positions.items()} == w.corrupt_positions


def test_fresh_prefix_stream_is_unchanged(word_tokenizer):
    """Digests of the fresh_prefix pairs taken on 2026-10-02, before shuffle_prefix
    existed (n=300, seed 0): adding a scheme moved nothing."""
    b = InductionBattery(word_tokenizer)

    def digest(bos):
        return hashlib.sha256(repr(b.pairs(300, 0, bos)).encode()).hexdigest()

    assert digest(False) == "0c43411f350197568cf8f6662ea32599cade1520b88ed67f02d4385394ed49f1"
    assert digest(True) == "f0beab52f1ef03857b767ded11fd96b5808538d506bcca91eba87c3f0170dd9e"


def test_shuffle_prefix_keeps_the_clean_stream(word_tokenizer):
    fresh = InductionBattery(word_tokenizer).pairs(300, 2, False)
    shuf = InductionBattery(word_tokenizer, "shuffle_prefix").pairs(300, 2, False)
    for f, s in zip(fresh, shuf):
        assert (s.clean_ids, s.answer_id, s.competitor_id, s.positions, s.template, s.meta) == \
               (f.clean_ids, f.answer_id, f.competitor_id, f.positions, f.template, f.meta)


def test_shuffle_prefix_pairs(word_tokenizer):
    b = InductionBattery(word_tokenizer, "shuffle_prefix")
    assert b.scheme == "shuffle_prefix" and b.corruption is SHUFFLE_PREFIX
    for pr in b.pairs(500, 0, False):
        i = int(pr.meta["i"])
        xs, ys = list(pr.clean_ids[:SEQ]), list(pr.corrupt_ids[:SEQ])
        assert sorted(ys) == sorted(xs) and ys != xs  # a permutation of the first repeat
        assert pr.corrupt_ids[SEQ:] == pr.clean_ids[SEQ:]  # second half identical
        assert not set(zip(ys, ys[1:])) & set(zip(xs, xs[1:]))  # no successor pair in the first repeat
        assert (xs[i - 1], xs[i]) not in set(zip(pr.corrupt_ids, pr.corrupt_ids[1:]))  # x_i -> x_{i+1} nowhere
        assert pr.answer_id in pr.corrupt_ids and pr.competitor_id in pr.corrupt_ids  # both still in context
        c = pr.corrupt_positions
        assert max(c["A1"], c["B1"], c["S_POS"]) < SEQ
        assert pr.corrupt_ids[c["A1"]] == xs[i - 1]
        assert pr.corrupt_ids[c["B1"]] == pr.answer_id == xs[i]
        assert pr.corrupt_ids[c["S_POS"]] == pr.competitor_id
        assert c["END"] == pr.positions["END"] and pr.corrupt_ids[c["END"]] == xs[i - 1]


def test_shuffle_prefix_bos_and_seeding(word_tokenizer):
    b = InductionBattery(word_tokenizer, "shuffle_prefix")
    bos = word_tokenizer.bos_token_id
    for a, w in zip(b.pairs(50, 1, False), b.pairs(50, 1, True)):
        assert w.corrupt_ids == (bos, *a.corrupt_ids)
        assert w.corrupt_positions == {k: v + 1 for k, v in a.corrupt_positions.items()}
    assert b.pairs(20, 3, False) == b.pairs(20, 3, False)
    assert b.pairs(20, 3, False) != b.pairs(20, 4, False)
