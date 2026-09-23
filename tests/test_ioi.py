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


# --- E1a additions: p_ABC counterpart, position labels, IOIBattery ---

import random  # noqa: E402

from src.lesion.battery import AlignmentError  # noqa: E402
from src.lesion.ioi import LABELS, P_ABC, IOIBattery, abc_counterpart, name_positions  # noqa: E402


def test_prompt_carries_place_and_object():
    p = generate_prompts(5, seed=0)[0]
    assert p.place in PLACES and p.obj in OBJECTS


def test_generation_stream_unchanged_by_new_fields():
    # The first prompt at seed 0, as generated before the place/obj fields
    # existed (recorded 2026-09-20). If this moves, the E0 stream has drifted.
    p = generate_prompts(1, seed=0)[0]
    assert (p.text, p.io, p.s, p.template_idx, p.order) == (
        "Then, Crystal and Bradley had a long argument. Afterwards Bradley said to Crystal",
        "Crystal", "Bradley", 12, "ABBA")


def test_abc_counterpart_keeps_template_and_swaps_three_names():
    rng = random.Random("p_ABC/0")
    for p in generate_prompts(200, seed=0):
        abc = abc_counterpart(p, rng)
        clean_words, abc_words = p.prompt.split(), abc.split()
        assert len(clean_words) == len(abc_words)
        diffs = [(c, a) for c, a in zip(clean_words, abc_words) if c != a]
        assert len(diffs) == 3, (p.prompt, abc)
        assert {c for c, _ in diffs} == {p.io, p.s}
        new = [a for _, a in diffs]
        assert len(set(new)) == 3 and not ({p.io, p.s} & set(new))
        assert all(n in NAMES for n in new)


def test_abc_counterpart_is_seeded():
    ps = generate_prompts(20, seed=0)
    a = [abc_counterpart(p, random.Random("p_ABC/0")) for p in ps]
    b = [abc_counterpart(p, random.Random("p_ABC/0")) for p in ps]
    assert a == b


def test_name_positions_labels():
    #        0  1  2  3  4  5  6
    ids = [10, 7, 11, 8, 12, 7, 13]  # S=7 at 1 and 5, IO=8 at 3
    assert name_positions(ids, io_id=8, s_id=7) == {"IO": 3, "S1": 1, "S1+1": 2, "S2": 5, "END": 6}


def test_name_positions_refuses_wrong_counts():
    with pytest.raises(AlignmentError):
        name_positions([7, 7, 7, 8], io_id=8, s_id=7)
    with pytest.raises(AlignmentError):
        name_positions([7, 8, 8, 7], io_id=8, s_id=7)


def test_ioi_battery_pairs_align(word_tokenizer):
    battery = IOIBattery(word_tokenizer)
    assert battery.name == "ioi" and battery.labels == LABELS and battery.corruption is P_ABC
    pairs = battery.pairs(200, seed=0, prepend_bos=False)
    assert len(pairs) == 200
    for pr in pairs:
        assert len(pr.clean_ids) == len(pr.corrupt_ids)
        assert set(pr.positions) == set(LABELS) and pr.positions == pr.corrupt_positions
        assert pr.positions["END"] == len(pr.clean_ids) - 1
        assert pr.clean_ids[pr.positions["IO"]] == pr.answer_id
        assert pr.clean_ids[pr.positions["S1"]] == pr.clean_ids[pr.positions["S2"]] == pr.competitor_id
        assert pr.positions["S1+1"] == pr.positions["S1"] + 1
        slots = {pr.positions[k] for k in ("IO", "S1", "S2")}
        new = {pr.corrupt_ids[i] for i in slots}
        assert len(new) == 3 and not (new & {pr.answer_id, pr.competitor_id})
        for i, (c, k) in enumerate(zip(pr.clean_ids, pr.corrupt_ids)):
            assert (c == k) == (i not in slots)
        assert pr.template.split("/")[0] == pr.meta["order"]


def test_ioi_battery_bos_shifts_every_label(word_tokenizer):
    battery = IOIBattery(word_tokenizer)
    no_bos = battery.pairs(50, seed=1, prepend_bos=False)
    bos = battery.pairs(50, seed=1, prepend_bos=True)
    for a, b in zip(no_bos, bos):
        assert b.clean_ids == (word_tokenizer.bos_token_id, *a.clean_ids)
        assert b.corrupt_ids == (word_tokenizer.bos_token_id, *a.corrupt_ids)
        assert b.positions == {k: v + 1 for k, v in a.positions.items()}
        assert b.corrupt_positions == {k: v + 1 for k, v in a.corrupt_positions.items()}


@pytest.mark.slow
def test_ioi_battery_aligns_under_the_real_tokenizer():
    from src.lesion.model import plain_tokenizer

    pairs = IOIBattery(plain_tokenizer()).pairs(500, seed=0, prepend_bos=False)
    assert len(pairs) == 500  # every alignment check inside pairs() passed


def test_ioi_battery_protocol_fields(word_tokenizer):
    b = IOIBattery(word_tokenizer)
    assert b.scheme == "p_ABC" and b.schemes[0] == "p_ABC" and b.corruption is P_ABC
    assert b.expected_direction == "positive" and b.default_prepend_bos is False
    with pytest.raises(ValueError):
        IOIBattery(word_tokenizer, "nope")


def test_default_scheme_stream_unchanged(word_tokenizer):
    a = IOIBattery(word_tokenizer).pairs(50, seed=0, prepend_bos=False)
    b = IOIBattery(word_tokenizer, "p_ABC").pairs(50, seed=0, prepend_bos=False)
    assert a == b
    # First p_ABC counterpart at seed 0, recorded 2026-09-23 before any E1b change.
    assert a[0].meta["corrupt_text"] == "Then, William and Jessica had a long argument. Afterwards Timothy said to"


# --- E1b additions: Wang's five App. A counterparts ---

from src.lesion.ioi import APP_A, SCHEMES, app_a_counterpart  # noqa: E402

SIGNALS = {  # the spec's table: (position signal, token signal)
    "rand_names": ("original", "uncorrelated"),
    "flip": ("inverted", "original"),
    "flip_rand": ("inverted", "uncorrelated"),
    "repl_flip": ("original", "inverted"),
    "repl": ("inverted", "inverted"),
}


def test_scheme_list_and_sources(word_tokenizer):
    assert IOIBattery.schemes == ("p_ABC", "rand_names", "flip", "flip_rand", "repl_flip", "repl")
    assert set(APP_A) == set(SIGNALS) and set(SCHEMES) == set(IOIBattery.schemes)
    for name in SIGNALS:
        c = SCHEMES[name]
        assert c.name == name and c.source == "wang-2022 App. A" and c.removes and c.inserts


@pytest.mark.parametrize("scheme", list(SIGNALS))
def test_app_a_signals_match_the_table(word_tokenizer, scheme):
    for pr in IOIBattery(word_tokenizer, scheme).pairs(200, seed=0, prepend_bos=False):
        slots = {k: pr.positions[k] for k in ("S1", "IO", "S2")}
        toks = {k: pr.corrupt_ids[i] for k, i in slots.items()}
        repeated = toks["S2"]
        rep_slots = {k for k, t in toks.items() if t == repeated}
        (once,) = {t for t in toks.values() if t != repeated}
        position = {frozenset({"S1", "S2"}): "original", frozenset({"IO", "S2"}): "inverted"}[frozenset(rep_slots)]
        c, s = pr.answer_id, pr.competitor_id
        if (repeated, once) == (s, c):
            token = "original"
        elif (repeated, once) == (c, s):
            token = "inverted"
        else:
            assert not ({repeated, once} & {c, s}), "a random name equals the clean IO or S"
            token = "uncorrelated"
        assert (position, token) == SIGNALS[scheme]
        assert len(pr.clean_ids) == len(pr.corrupt_ids)
        for i, (a, b) in enumerate(zip(pr.clean_ids, pr.corrupt_ids)):
            if i not in slots.values():
                assert a == b, (scheme, i)


@pytest.mark.parametrize("scheme", list(SIGNALS))
def test_app_a_corrupt_labels_follow_roles(word_tokenizer, scheme):
    for pr in IOIBattery(word_tokenizer, scheme).pairs(100, seed=1, prepend_bos=True):
        cp, ids = pr.corrupt_positions, pr.corrupt_ids
        assert ids[cp["S1"]] == ids[cp["S2"]] != ids[cp["IO"]]
        assert ids.count(ids[cp["IO"]]) == 1 and ids.count(ids[cp["S1"]]) == 2
        assert cp["S1"] < cp["S2"] and cp["S1+1"] == cp["S1"] + 1
        assert cp["END"] == pr.positions["END"] == len(ids) - 1
        if scheme == "flip":  # the names moved, so the labels moved with them
            assert (cp["IO"], cp["S1"]) == (pr.positions["S1"], pr.positions["IO"])


def test_app_a_is_seeded_and_names_are_fresh():
    p = generate_prompts(1, seed=0)[0]
    a = app_a_counterpart(p, "rand_names", random.Random("rand_names/0"))
    assert a == app_a_counterpart(p, "rand_names", random.Random("rand_names/0"))
    text, once, repeated = a
    assert once != repeated and not ({once, repeated} & {p.io, p.s}) and {once, repeated} <= set(NAMES)
    assert text.split().count(repeated) == 2 and text.split().count(once) == 1
