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


from src.lesion.evaluators import composition_scores, random_baseline  # noqa: E402


def rand_weights(L=3, H=2, d=6, r=2, seed=0):
    g = torch.Generator().manual_seed(seed)
    W_Q, W_K, W_V = (torch.randn(L, H, d, r, generator=g, dtype=torch.float64) for _ in range(3))
    return W_Q, W_K, W_V, torch.randn(L, H, r, d, generator=g, dtype=torch.float64)


def test_composition_equals_dense_products():
    W_Q, W_K, W_V, W_O = rand_weights()
    got = composition_scores(W_Q, W_K, W_V, W_O)
    fro = torch.linalg.matrix_norm
    for l1 in range(3):
        for h1 in range(2):
            ov1 = W_V[l1, h1] @ W_O[l1, h1]
            for l2 in range(3):
                for h2 in range(2):
                    if l2 <= l1:
                        assert all(torch.isnan(got[m][l1, h1, l2, h2]) for m in "QKV")
                        continue
                    qk2 = W_Q[l2, h2] @ W_K[l2, h2].T
                    ov2 = W_V[l2, h2] @ W_O[l2, h2]
                    exp = {"K": fro(ov1 @ qk2.T) / (fro(ov1) * fro(qk2)),
                           "Q": fro(ov1 @ qk2) / (fro(ov1) * fro(qk2)),
                           "V": fro(ov1 @ ov2) / (fro(ov1) * fro(ov2))}
                    for m in "QKV":
                        assert got[m][l1, h1, l2, h2].item() == pytest.approx(exp[m].item(), rel=1e-10)


def test_composition_on_constructed_overlap():
    """h1 reads e0 and writes e1. h2's key reads e1 (full K-composition); its
    query and value read e3 and e2, orthogonal to what h1 writes."""
    e = torch.eye(4, dtype=torch.float64)
    W_Q, W_K, W_V = (torch.zeros(2, 1, 4, 1, dtype=torch.float64) for _ in range(3))
    W_O = torch.zeros(2, 1, 1, 4, dtype=torch.float64)
    W_V[0, 0, :, 0], W_O[0, 0, 0, :] = e[0], e[1]
    W_K[1, 0, :, 0], W_Q[1, 0, :, 0], W_V[1, 0, :, 0], W_O[1, 0, 0, :] = e[1], e[3], e[2], e[0]
    got = composition_scores(W_Q, W_K, W_V, W_O)
    assert got["K"][0, 0, 1, 0].item() == pytest.approx(1.0)
    assert got["Q"][0, 0, 1, 0].item() == 0.0 and got["V"][0, 0, 1, 0].item() == 0.0


@torch.no_grad()
def test_composition_matches_transformer_lens(tiny_model):
    m = tiny_model
    got = composition_scores(m.W_Q, m.W_K, m.W_V, m.W_O)
    for mode in "QKV":
        tl = m.all_composition_scores(mode).double().cpu()
        assert torch.allclose(got[mode][0, :, 1, :], tl[0, :, 1, :], rtol=1e-4, atol=1e-7), mode


def test_composition_is_scale_invariant():
    W_Q, W_K, W_V, W_O = rand_weights(seed=3)
    a = composition_scores(W_Q, W_K, W_V, W_O)
    b = composition_scores(2 * W_Q, 0.5 * W_K, 3 * W_V, 7 * W_O)
    for m in "QKV":
        assert torch.allclose(a[m], b[m], equal_nan=True)


def test_random_baseline_is_seeded():
    a = random_baseline(16, 4, draws=20, seed=0)
    assert a == random_baseline(16, 4, draws=20, seed=0) and a != random_baseline(16, 4, draws=20, seed=1)
    for m in "QKV":
        assert set(a[m]) == {"mean", "sd", "draws", "seed"} and 0 < a[m]["mean"] < 1 and a[m]["draws"] == 20
