"""Induction pairs [olsson-2022 §Data Collection (3)], with the spec's stated departures."""

import pytest

from src.lesion.induction import FRESH_PREFIX, HI, I_MAX, LABELS, LO, SEQ, InductionBattery


def test_constants_and_fields(word_tokenizer):
    b = InductionBattery(word_tokenizer)
    assert (LO, HI, SEQ, I_MAX) == (1000, 45000, 25, 22)
    assert b.labels == LABELS == ("A1", "B1", "S_POS", "END")
    assert b.schemes == ("fresh_prefix",) and b.corruption is FRESH_PREFIX
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
