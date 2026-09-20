"""Checks on the ported p_IOI generator. The tokenizer test needs the model's
tokenizer (network on first run), the rest is pure."""

import re

import pytest

from src.lesion.ioi import ABBA_TEMPLATES, BABA_TEMPLATES, NAMES, OBJECTS, PLACES, generate_prompts


def test_template_counts_match_paper():
    assert len(BABA_TEMPLATES) == 15
    assert len(ABBA_TEMPLATES) == 15


def test_abba_swaps_only_first_clause():
    assert ABBA_TEMPLATES[0] == "Then, [A] and [B] went to the [PLACE]. [B] gave a [OBJECT] to [A]"
    for baba, abba in zip(BABA_TEMPLATES, ABBA_TEMPLATES):
        # The released code's own construction: swap the first [B] and first [A].
        expected = baba.replace("[B]", "[X]", 1).replace("[A]", "[B]", 1).replace("[X]", "[A]", 1)
        assert abba == expected
        assert abba.endswith("[A]") and abba.count("[A]") == 2 and abba.count("[B]") == 2
        assert abba.index("[A]") < abba.index("[B]")


def test_released_list_sizes():
    # Deliberately pins the *released* sizes, which differ from the paper text
    # (100 names, 20 places, 20 objects). See the module docstring.
    assert len(NAMES) == 99 and len(set(NAMES)) == 99
    assert len(PLACES) == 8 and len(OBJECTS) == 8


def test_generation_is_seeded_and_well_formed():
    a = generate_prompts(50, seed=3)
    b = generate_prompts(50, seed=3)
    assert a == b
    assert a != generate_prompts(50, seed=4)
    for p in a:
        assert p.io != p.s
        assert p.text.endswith(" " + p.io)
        assert p.text == p.prompt + " " + p.io
        words = re.findall(r"[A-Za-z]+", p.text)
        assert words.count(p.s) == 2 and words.count(p.io) == 2
        words = re.findall(r"[A-Za-z]+", p.prompt)
        assert words.count(p.s) == 2 and words.count(p.io) == 1
        assert p.order in ("BABA", "ABBA") and 0 <= p.template_idx < 15


@pytest.mark.slow
def test_every_word_is_a_single_gpt2_token():
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained("gpt2")
    for w in NAMES + PLACES + OBJECTS:
        assert len(tok(" " + w).input_ids) == 1, w
