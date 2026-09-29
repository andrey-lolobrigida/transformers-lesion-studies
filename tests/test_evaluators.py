"""Evaluators: hand-built attention patterns with known scores, a brute-force
copy check, and composition scores against dense products and TransformerLens."""

import pytest
import torch

from src.lesion.evaluators import (
    attention_scores, copy_scores, pattern_score_sums, repeated_random_tokens, score_queries,
)


def test_repeated_random_tokens():
    a = repeated_random_tokens(3, 5, 50, seed=0)
    assert a.shape == (3, 10) and torch.equal(a[:, :5], a[:, 5:])
    assert torch.equal(a, repeated_random_tokens(3, 5, 50, seed=0))
    assert not torch.equal(a, repeated_random_tokens(3, 5, 50, seed=1))
    b = repeated_random_tokens(3, 5, 50, seed=0, bos_id=49)
    assert b.shape == (3, 11) and (b[:, 0] == 49).all() and torch.equal(b[:, 1:], a)  # same draw, shifted


def test_score_queries():
    q = score_queries(100)
    assert q["previous_token"] == (list(range(1, 200)), 1)
    assert q["induction"] == (list(range(100, 200)), 99)
    assert q["duplicate"] == (list(range(100, 200)), 100)


def hand_pattern(S: int, start: int) -> torch.Tensor:
    """[batch 2, head 3, T, T]: head 0 attends to the previous token, head 1 is
    an induction head (j -> j-(S-1) in the second half), head 2 a duplicate
    head (j -> j-S). Elsewhere a head attends to itself. ``start`` pads a BOS
    row and column in front."""
    T = 2 * S
    P = torch.zeros(3, T + start, T + start)
    for j in range(T):
        keys = (j - 1 if j >= 1 else j, j - (S - 1) if j >= S else j, j - S if j >= S else j)
        for h, k in enumerate(keys):
            P[h, start + j, start + k] = 1.0
    return P.expand(2, 3, T + start, T + start).clone()


@pytest.mark.parametrize("start", [0, 1])
def test_pattern_scores_on_known_patterns(start):
    S = 4
    sums = pattern_score_sums(hand_pattern(S, start), S, start)
    counts = {k: 2 * len(js) for k, (js, _) in score_queries(S).items()}
    got = {k: (v / counts[k]).tolist() for k, v in sums.items()}
    assert got["previous_token"] == [1.0, 0.0, 0.0]
    assert got["induction"] == [0.0, 1.0, 0.0]
    assert got["duplicate"] == [0.0, 0.0, 1.0]


@torch.no_grad()
@pytest.mark.parametrize("bos", [False, True])
def test_attention_scores_match_a_loop(tiny_model, bos):
    S, start = 5, int(bos)
    toks = repeated_random_tokens(3, S, 50, seed=2, bos_id=0 if bos else None)
    got = attention_scores(tiny_model, toks, S, start, batch_size=2)
    _, cache = tiny_model.run_with_cache(toks)
    for name, (js, off) in score_queries(S).items():
        for l in range(2):
            pat = cache[f"blocks.{l}.attn.hook_pattern"]
            for h in range(2):
                vals = [pat[b, h, start + j, start + j - off].item() for b in range(3) for j in js]
                assert got[name][l, h].item() == pytest.approx(sum(vals) / len(vals), abs=1e-6)


@torch.no_grad()
def test_copy_scores_match_a_brute_force_loop(tiny_model):
    S = 4
    toks = repeated_random_tokens(3, S, 50, seed=1)
    got = copy_scores(tiny_model, toks, S, start=0, batch_size=2)
    _, cache = tiny_model.run_with_cache(toks)
    exp = torch.zeros(2, 2, dtype=torch.float64)
    for b in range(3):
        for j in range(S, 2 * S - 1):
            for l in range(2):
                for h in range(2):
                    out = cache[f"blocks.{l}.attn.hook_z"][b, j, h] @ tiny_model.W_O[l, h]
                    exp[l, h] += float(out @ tiny_model.W_U[:, toks[b, j + 1]])
    exp /= 3 * (S - 1)
    assert torch.allclose(got.double(), exp, atol=1e-5)
