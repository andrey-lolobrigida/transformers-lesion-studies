"""Induction pairs: a repeated sequence of random tokens, read where the
second copy predicts the successor of its last token.

Stimulus copied from Olsson et al. [olsson-2022 §Data Collection (3)]: 25
random tokens, distinct within the sequence, excluding the most and least
common tokens; BOS prepended (through the harness's ``prepend_bos``, never by
this generator). The source gives no thresholds for the exclusion, so the rule
is ours: token ids uniform in [LO, HI), the GPT-2 BPE id standing in for
frequency rank (low ids are bytes and early, frequent merges; the highest ids
are late, rare merges). Departure: 2 repeats rather than 4, the second cut
after x_i. Token ids are used directly; nothing is decoded or re-encoded.

Metric: logit difference at END (rule 5). Olsson's in-context learning score
is a loss and is not used.

Second scheme, ``shuffle_prefix`` (E3, D-016 item 6; ours, unsourced): the
first repeat's 25 tokens permuted so that no x_k is immediately followed by
x_{k+1} there. It removes the successor relation and keeps every token in
context, so its contrast with ``fresh_prefix`` (which removes both) separates
the two. The clean stream is shared: each scheme draws its corruption from its
own RNG."""

from __future__ import annotations

import random

from src.lesion.battery import Corruption, PromptPair, resolve_scheme, with_bos

LO, HI = 1000, 45000  # sampled id range, a frequency proxy (ours)
SEQ = 25  # tokens per repeat [olsson-2022]
I_MAX = 22  # i uniform in 1..I_MAX, so j = i+3..25 is never empty

# A1: x_i in the first repeat; B1: x_{i+1} in the first repeat (where c sits);
# S_POS: x_j in the first repeat (where s sits); END: x_i in the second repeat.
LABELS = ("A1", "B1", "S_POS", "END")

FRESH_PREFIX = Corruption(
    name="fresh_prefix",
    removes="the earlier occurrence of x_i and its successor (what induction copies), and the in-context "
            "occurrence of both c and s",
    inserts="an equally long unrepeated random prefix: 25 fresh token ids under the same sampling rule, "
            "distinct from each other and from every clean token; length, positions, the second half and the "
            "sampling distribution kept. Expected corrupt ld near 0 by symmetry",
    source="olsson-2022 §Data Collection (3) (stimulus); corruption ours (E1b spec)",
)

SHUFFLE_PREFIX = Corruption(
    name="shuffle_prefix",
    removes="the successor relation induction copies: the first repeat's 25 tokens are permuted so that no x_k is "
            "immediately followed by x_{k+1} there; x_i -> x_{i+1}, the pair END needs, then occurs nowhere in the "
            "prompt",
    inserts="the same 25 tokens in a constrained uniform order (rejection sampling); every token's presence in "
            "context kept, including c and s; length, the second half, END and the template key kept. A1, B1 and "
            "S_POS move to where x_i, x_{i+1} and x_j sit after the permutation. Expected corrupt ld near 0 by "
            "symmetry (a prediction, measured by the gate)",
    source="ours, unsourced (E3 spec; D-016 item 6)",
)
SCHEMES = {"fresh_prefix": FRESH_PREFIX, "shuffle_prefix": SHUFFLE_PREFIX}


def _fresh(rng: random.Random, k: int, exclude) -> list[int]:
    """``k`` distinct ids uniform in [LO, HI), none in ``exclude``."""
    seen = set(exclude)
    out: list[int] = []
    while len(out) < k:
        t = rng.randrange(LO, HI)
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _shuffle_no_successor(rng: random.Random, xs: list[int]) -> list[int]:
    """A permutation of ``xs`` in which no ``xs[k]`` is immediately followed by
    ``xs[k+1]``, by rejection: about 38% of uniform permutations of 25 distinct
    tokens qualify, so a few draws suffice."""
    successor = dict(zip(xs, xs[1:]))
    while True:
        ys = list(xs)
        rng.shuffle(ys)
        if all(successor.get(a) != b for a, b in zip(ys, ys[1:])):
            return ys


class InductionBattery:
    """Repeated random tokens, corrupt ``fresh_prefix`` (default) or ``shuffle_prefix``. Implements ``battery.Battery``."""

    name = "induction"
    labels = LABELS
    schemes = ("fresh_prefix", "shuffle_prefix")
    expected_direction = "positive"
    default_prepend_bos = True  # Olsson: omitting BOS gave anomalously low scores
    template_set = (f"olsson-2022 §Data Collection (3) with departures: {SEQ} distinct token ids uniform in "
                    f"[{LO}, {HI}) as a frequency proxy (ours); 2 repeats, the second cut after x_i, "
                    f"i uniform in 1..{I_MAX}; competitor x_j, j uniform in i+3..{SEQ}")

    def __init__(self, tokenizer, scheme: str | None = None) -> None:
        self.bos_id = tokenizer.bos_token_id
        self.scheme = resolve_scheme(self.schemes, scheme)
        self.corruption = SCHEMES[self.scheme]

    def pairs(self, n: int, seed: int, prepend_bos: bool) -> list[PromptPair]:
        rng = random.Random(seed)
        crng = random.Random(f"{self.scheme}/{seed}")  # the clean stream never depends on the corruption
        out = []
        for _ in range(n):
            xs = _fresh(rng, SEQ, ())
            i = rng.randint(1, I_MAX)
            j = rng.randint(i + 3, SEQ)
            pos = {"A1": i - 1, "B1": i, "S_POS": j - 1, "END": SEQ + i - 1}
            if self.scheme == "fresh_prefix":
                ys = _fresh(crng, SEQ, xs)
                cpos = dict(pos)
            else:
                ys = _shuffle_no_successor(crng, xs)
                cpos = {"A1": ys.index(xs[i - 1]), "B1": ys.index(xs[i]), "S_POS": ys.index(xs[j - 1]),
                        "END": SEQ + i - 1}
            clean, corrupt = xs + xs[:i], ys + xs[:i]
            if prepend_bos:
                clean, pos = with_bos(clean, pos, self.bos_id)
                corrupt, cpos = with_bos(corrupt, cpos, self.bos_id)
            out.append(PromptPair(
                clean_ids=tuple(clean), corrupt_ids=tuple(corrupt), answer_id=xs[i], competitor_id=xs[j - 1],
                positions=pos, corrupt_positions=cpos, template=f"i{i}", meta={"i": str(i), "j": str(j)},
            ))
        return out
