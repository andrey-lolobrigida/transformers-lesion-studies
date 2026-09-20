"""The battery interface: alignment is checked at construction, BOS shifts every label."""

from types import SimpleNamespace

import pytest

from src.lesion.battery import AlignmentError, PromptPair, encode, with_bos


def make_pair(**overrides):
    kw = dict(
        clean_ids=(5, 6, 7, 8), corrupt_ids=(5, 9, 7, 8), answer_id=1, competitor_id=2,
        positions={"X": 1, "END": 3}, corrupt_positions={"X": 1, "END": 3},
        template="A", meta={},
    )
    kw.update(overrides)
    return PromptPair(**kw)


def test_pair_accepts_aligned_inputs():
    p = make_pair()
    assert p.positions["END"] == 3


def test_pair_refuses_length_mismatch():
    with pytest.raises(AlignmentError):
        make_pair(corrupt_ids=(5, 9, 7))


def test_pair_refuses_label_set_mismatch():
    with pytest.raises(AlignmentError):
        make_pair(corrupt_positions={"END": 3})


def test_pair_requires_end_label():
    with pytest.raises(AlignmentError):
        make_pair(positions={"X": 1}, corrupt_positions={"X": 1})


def test_pair_refuses_out_of_range_index():
    with pytest.raises(AlignmentError):
        make_pair(positions={"X": 1, "END": 4}, corrupt_positions={"X": 1, "END": 4})


def test_with_bos_shifts_every_label_by_one():
    ids, pos = with_bos([5, 6, 7], {"A": 0, "END": 2}, bos_id=50256)
    assert ids == [50256, 5, 6, 7]
    assert pos == {"A": 1, "END": 3}


class BosPrependingTokenizer:
    bos_token_id = 0

    def __call__(self, text, add_special_tokens=False):
        return SimpleNamespace(input_ids=[0, 1, 2])


class PlainTokenizer:
    bos_token_id = 0

    def __call__(self, text, add_special_tokens=False):
        return SimpleNamespace(input_ids=[1, 2])


def test_encode_refuses_a_tokenizer_that_prepends_bos():
    with pytest.raises(AlignmentError):
        encode(BosPrependingTokenizer(), "hello")


def test_encode_returns_a_plain_list():
    assert encode(PlainTokenizer(), "hello") == [1, 2]
