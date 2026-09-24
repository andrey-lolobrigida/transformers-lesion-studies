"""Subject-verb agreement pairs: ``The {N1} {prep} the {N2}``, read at N2,
where the next token is the verb.

D-013 fallback item, **unsourced**. Every choice below is ours (the agreement
addendum to D-013, 2026-09-24): the item departs from reproduction-first and
no published number is checked against it. The candidate noun list is ours
too (E1b agreement plan, 2026-09-24).

Nouns: animate common nouns with regular ``-s`` plurals, kept only if the
singular and the plural are each one token with a leading space; a noun that
fails is dropped in both numbers. Verbs: ``is``/``are`` and ``has``/``have``,
present tense, drawn per prompt. The verb never appears in the prompt: it only
picks the two logits ``ld`` reads (``c`` the form agreeing with N1, ``s`` the
other form). N2 is the attractor, a different noun that shares N1's number
(congruent) or not (incongruent), 50/50. Template key ``{prep}/{congruency}``;
subject number is deliberately not in it, but prompts come in blocks of 16,
each block one shuffle of every (preposition, congruency, subject number)
cell, so at n a multiple of 16 every template has exactly n/8 prompts, half
singular and half plural, and each template's mean-ablation reference is
exactly number-balanced; verb pair drawn independently per prompt. This
replaced independent 50/50 draws on 2026-09-24 (D-013).

Prompts are concatenations of single-token ids; nothing is decoded and
re-encoded. BOS is added only through ``prepend_bos``."""

from __future__ import annotations

import random

from src.lesion.battery import AlignmentError, Corruption, PromptPair, encode, resolve_scheme, with_bos
from src.lesion.counterfact import single_token

NOUNS = (
    "dog", "cat", "horse", "cow", "pig", "goat", "bird", "duck", "owl", "eagle", "bear", "lion", "tiger",
    "rabbit", "snake", "frog", "monkey", "chicken",
    "teacher", "doctor", "nurse", "farmer", "lawyer", "student", "soldier", "driver", "singer", "writer",
    "artist", "baker", "pilot", "officer", "worker", "player", "painter", "manager", "guard", "author", "actor",
    "dancer", "engineer", "visitor",
    "friend", "neighbor", "guest", "boy", "girl", "king", "queen", "parent",
)
PREPS = ("near", "behind", "beside", "with")
VERBS = (("is", "are"), ("has", "have"))  # (singular form, plural form)
LABELS = ("N1", "PREP", "N2", "END")  # END is N2's index: the verb comes next

_SOURCE = "ours (D-013 fallback; unsourced)"
NUMBER_FLIP = Corruption(
    name="number_flip",
    removes="the subject's grammatical number: N1 replaced by its own other-number form (dog <-> dogs)",
    inserts="the opposite number on the same noun; preposition, attractor and length kept, so congruent prompts "
            "become incongruent and back. c and s stay the clean labels, so the corrupt prompt favours s: expected "
            "corrupt ld near minus the clean ld, fraction removed near 2 (D-014 item 2)",
    source=_SOURCE)
NUMBER_FLIP_ALL = Corruption(
    name="number_flip_all",
    removes="the grammatical number of both nouns: N1 and N2 each replaced by their own other-number form",
    inserts="the opposite number on both nouns; congruency and length kept. c and s stay the clean labels: "
            "expected fraction removed near 2, as number_flip, with the attractor's number moved too",
    source=_SOURCE)
SCHEMES = {"number_flip": NUMBER_FLIP, "number_flip_all": NUMBER_FLIP_ALL}


def kept_nouns(tokenizer) -> list[tuple[str, int, int]]:
    """(singular, singular id, plural id) for every candidate whose two forms are each one token."""
    out = []
    for w in NOUNS:
        sg, pl = single_token(tokenizer, w), single_token(tokenizer, w + "s")
        if sg is not None and pl is not None:
            out.append((w, sg, pl))
    return out


def _one(tokenizer, word: str) -> int:
    t = single_token(tokenizer, word)
    if t is None:
        raise AlignmentError(f"{' ' + word!r} is not one token; every agreement prompt needs it to be")
    return t


_CELLS = [(k, congruent, plural) for k in range(len(PREPS)) for congruent in (True, False) for plural in (True, False)]


class AgreementBattery:
    """Subject-verb agreement across a prepositional-phrase attractor, corrupt
    ``number_flip``. Implements ``battery.Battery``."""

    name = "agreement"
    labels = LABELS
    schemes = ("number_flip", "number_flip_all")
    expected_direction = "positive"
    default_prepend_bos = True  # the prompts are 5 tokens; without BOS the first position is a content word
    breakdown_keys = ("congruency", "verb", "subject_number")  # ungated gate readings (e1b_gate.breakdown)

    def __init__(self, tokenizer, scheme: str | None = None) -> None:
        self.bos_id = tokenizer.bos_token_id
        self.scheme = resolve_scheme(self.schemes, scheme)
        self.corruption = SCHEMES[self.scheme]
        start = encode(tokenizer, "The")
        if len(start) != 1:
            raise AlignmentError("'The' is not one token")
        self.the_start, self.the_mid = start[0], _one(tokenizer, "the")
        self.prep_ids = [_one(tokenizer, p) for p in PREPS]
        self.verb_ids = [(_one(tokenizer, sg), _one(tokenizer, pl)) for sg, pl in VERBS]
        self.nouns = kept_nouns(tokenizer)
        if len(self.nouns) < 2:
            raise ValueError(f"only {len(self.nouns)} candidate nouns are single tokens in both numbers")
        self.template_set = (
            f"ours (D-013 fallback, unsourced; no published number is checked against it): "
            f"'The {{N1}} {{prep}} the {{N2}}' -> verb; {len(self.nouns)} of {len(NOUNS)} candidate nouns kept "
            f"(regular -s plurals, both forms one token); prep in {PREPS}; verb pair in {VERBS}, drawn per prompt; "
            f"N2 a different noun; (prep, congruency, subject number) balanced exactly in blocks of 16; "
            f"template key prep/congruency")

    def pairs(self, n: int, seed: int, prepend_bos: bool) -> list[PromptPair]:
        rng = random.Random(seed)
        flip_n2 = self.scheme == "number_flip_all"
        out = []
        block: list[tuple[int, bool, bool]] = []
        for _ in range(n):
            if not block:
                block = list(_CELLS)
                rng.shuffle(block)
            k, congruent, plural = block.pop()
            a, b = rng.sample(range(len(self.nouns)), 2)
            v = rng.randrange(len(VERBS))
            (w1, sg1, pl1), (w2, sg2, pl2) = self.nouns[a], self.nouns[b]
            n2_plural = plural if congruent else not plural
            form1 = lambda pl: pl1 if pl else sg1  # noqa: E731
            form2 = lambda pl: pl2 if pl else sg2  # noqa: E731
            clean = [self.the_start, form1(plural), self.prep_ids[k], self.the_mid, form2(n2_plural)]
            corrupt = [self.the_start, form1(not plural), self.prep_ids[k], self.the_mid,
                       form2(not n2_plural if flip_n2 else n2_plural)]
            pos = {"N1": 1, "PREP": 2, "N2": 4, "END": 4}
            cpos = dict(pos)
            if prepend_bos:
                clean, pos = with_bos(clean, pos, self.bos_id)
                corrupt, cpos = with_bos(corrupt, cpos, self.bos_id)
            v_sg, v_pl = self.verb_ids[v]
            c, s = (v_pl, v_sg) if plural else (v_sg, v_pl)
            congruency = "congruent" if congruent else "incongruent"
            out.append(PromptPair(
                clean_ids=tuple(clean), corrupt_ids=tuple(corrupt), answer_id=c, competitor_id=s,
                positions=pos, corrupt_positions=cpos, template=f"{PREPS[k]}/{congruency}",
                meta={"n1": w1, "n2": w2, "prep": PREPS[k], "subject_number": "plural" if plural else "singular",
                      "congruency": congruency, "verb": "/".join(VERBS[v])},
            ))
        return out
