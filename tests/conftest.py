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


@pytest.fixture
def word_tokenizer() -> WordTokenizer:
    return WordTokenizer()


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
