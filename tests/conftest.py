# tests/conftest.py
"""Shared fixtures. Everything here runs on CPU with no network."""

from __future__ import annotations

import random
import re
from types import SimpleNamespace

import pytest
import torch

from src.lesion.battery import Corruption, PromptPair, with_bos


class WordTokenizer:
    """Offline stand-in for the GPT-2 tokenizer. Every maximal run of
    non-space characters, together with the space before it, is one token, so
    ' Mary' is one id and ' store.' another. That is enough for the IOI
    alignment and label tests: names are always preceded by a space and
    followed by a space in the released templates, so a name is one token
    here as it is in GPT-2."""

    bos_token_id = 0

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}

    def __call__(self, text: str, add_special_tokens: bool = False):
        pieces = re.findall(r" ?\S+", text)
        ids = [self.vocab.setdefault(p, len(self.vocab) + 1) for p in pieces]
        return SimpleNamespace(input_ids=ids)

    def decode(self, ids) -> str:
        inv = {v: k for k, v in self.vocab.items()}
        return "".join(inv[i] for i in ids)


@pytest.fixture
def word_tokenizer() -> WordTokenizer:
    return WordTokenizer()


def make_counterfact(tok):
    """Hand-built CounterFact records plus a fake greedy generator, for the
    counterfact and factual tests. Expected build() counts, by construction:
    records 38; multi_token_target 1 (a two-token object); pool 37;
    not_known 1; no_partner 2 (T3: each record's only partner has the other's
    target_new as its true object); 34 known with a partner; templates
    T1/empty-suffix 30 (admitted, exactly the floor), T1/suffix " the" 1,
    T2/empty-suffix 3 (not admitted)."""
    t1, t2, t3 = "The capital of {} is", "{} works in", "{} was born in"
    objects = ["Paris", "Rome", "Oslo"]

    def rec(case_id, template, subject, true, new):
        return {"case_id": case_id, "requested_rewrite": {
            "prompt": template, "relation_id": "P0", "subject": subject,
            "target_true": {"str": true, "id": "Q0"}, "target_new": {"str": new, "id": "Q0"}}}

    records = [rec(k, t1, f"Subj{k}", objects[k % 3], "Berlin") for k in range(32)]
    records.append(rec(32, t1, "Subj32", "New York", "Berlin"))  # two-token object
    records += [rec(40 + k, t2, f"Worker{k}", objects[k], "Berlin") for k in range(3)]
    records += [rec(50, t3, "Born0", "Paris", "Rome"), rec(51, t3, "Born1", "Rome", "Paris")]

    def ids(text):
        return tok(text).input_ids

    the = ids(" the")[0]
    plan = {}
    for r in records:
        rr = r["requested_rewrite"]
        o = ids(" " + rr["target_true"]["str"])
        prompt = tuple(ids(rr["prompt"].replace("{}", rr["subject"])))
        if r["case_id"] == 0:
            plan[prompt] = [the] * 10  # never names o: not known
        elif r["case_id"] == 1:
            plan[prompt] = [the, o[0]] + [the] * 8  # known, with suffix " the"
        else:
            plan[prompt] = [o[0]] + [the] * 9

    def generate(prompts):
        return [plan[tuple(p)] for p in prompts]

    return records, generate


@pytest.fixture
def tiny_model():
    """Two layers, two heads, d_model 16, random weights, seeded. CPU."""
    from transformer_lens import HookedTransformer, HookedTransformerConfig

    cfg = HookedTransformerConfig(
        n_layers=2, n_heads=2, d_model=16, d_head=8, d_mlp=64, d_vocab=50, n_ctx=16,
        act_fn="gelu", seed=0, normalization_type="LN", device="cpu",
    )
    model = HookedTransformer(cfg)
    model.eval()
    return model


class TinyBattery:
    """Hand-built pairs for the tiny model: length-6 token sequences over the
    tiny vocab (ids 3..49, so answer 1, competitor 2 and BOS 0 never occur in
    a prompt); the corrupt twin differs at position 2 only; labels X (=2) and
    END (=5); templates alternate "A"/"B" so per-template code paths run.
    ``identical=True`` makes every clean prompt the same sequence, for the
    mean-reference identity test."""

    name = "tiny"
    labels = ("X", "END")
    schemes = ("swap-2",)
    expected_direction = "positive"
    default_prepend_bos = False
    template_set = "tests/conftest.py TinyBattery"
    corruption = Corruption(
        name="swap-2", removes="the token at position 2", inserts="a different token at position 2",
        source="tests/conftest.py",
    )

    def __init__(self, length: int = 6, vocab: int = 50, identical: bool = False) -> None:
        self.length, self.vocab, self.identical = length, vocab, identical

    def pairs(self, n: int, seed: int, prepend_bos: bool) -> list[PromptPair]:
        rng = random.Random(seed)
        fixed = [rng.randrange(3, self.vocab) for _ in range(self.length)]
        out = []
        for i in range(n):
            clean = list(fixed) if self.identical else [rng.randrange(3, self.vocab) for _ in range(self.length)]
            corrupt = list(clean)
            corrupt[2] = 3 + (clean[2] - 3 + 1) % (self.vocab - 3)  # always a different id in 3..vocab-1
            pos = {"X": 2, "END": self.length - 1}
            cpos = dict(pos)
            if prepend_bos:
                clean, pos = with_bos(clean, pos, 0)
                corrupt, cpos = with_bos(corrupt, cpos, 0)
            out.append(PromptPair(
                clean_ids=tuple(clean), corrupt_ids=tuple(corrupt), answer_id=1, competitor_id=2,
                positions=pos, corrupt_positions=cpos, template="A" if i % 2 == 0 else "B",
                meta={"i": str(i)},
            ))
        return out


@pytest.fixture
def tiny_battery() -> TinyBattery:
    return TinyBattery()


@pytest.fixture
def toks() -> torch.Tensor:
    """A fixed [1, 7] token batch for the tiny model."""
    g = torch.Generator().manual_seed(0)
    return torch.randint(3, 50, (1, 7), generator=g)
