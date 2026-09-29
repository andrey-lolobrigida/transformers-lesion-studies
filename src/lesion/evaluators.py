"""Head evaluators for E2's induction targets (I1, I2): attention scores on
repeated random tokens [wang-2022 App. H, App. I], the copy check [wang-2022
App. H, Fig. 17], and Q-, K-, V-composition scores [elhage-2021, "Two-Layer
Attention Only Transformers" and the Correction]. Pure functions of the
model's weights, attention patterns or head outputs; nothing here ablates.

Stimulus (Wang App. H): sequences A of ``half_len`` token ids drawn uniformly
from the whole vocabulary, doubled to AA. Wang states neither BOS nor token
exclusions; the gated setting has neither (E2 spec, I1). Positions below are
AA indices j; with BOS every position shifts by one (``start``)."""

from __future__ import annotations

import random
import statistics

import torch
from torch import Tensor


def repeated_random_tokens(n_seq: int, half_len: int, d_vocab: int, seed: int, bos_id: int | None = None) -> Tensor:
    """``[n_seq, 2*half_len]`` (``+1`` with BOS): each row A A, A uniform over
    ``range(d_vocab)`` with replacement. The BOS variant is the same draw."""
    rng = random.Random(seed)
    rows = []
    for _ in range(n_seq):
        a = [rng.randrange(d_vocab) for _ in range(half_len)]
        rows.append(([] if bos_id is None else [bos_id]) + a + a)
    return torch.tensor(rows)


def score_queries(half_len: int) -> dict[str, tuple[list[int], int]]:
    """score -> (query AA indices, key offset). Previous token: every j >= 1,
    key j-1 ("the off-diagonal"). Induction: second-half j, key j-(S-1), the
    token after the first occurrence. Duplicate: second-half j, key j-S, the
    first occurrence."""
    S = half_len
    return {
        "previous_token": (list(range(1, 2 * S)), 1),
        "induction": (list(range(S, 2 * S)), S - 1),
        "duplicate": (list(range(S, 2 * S)), S),
    }


def pattern_score_sums(pattern: Tensor, half_len: int, start: int) -> dict[str, Tensor]:
    """Per head (``pattern`` is ``[batch, head, q, k]``): the attention from
    each score's queries to query-minus-offset, summed over batch and queries."""
    out = {}
    for name, (js, offset) in score_queries(half_len).items():
        q = torch.tensor([start + j for j in js], device=pattern.device)
        out[name] = pattern[:, :, q, q - offset].sum(dim=(0, 2))
    return out


@torch.no_grad()
def attention_scores(model, toks: Tensor, half_len: int, start: int, batch_size: int) -> dict[str, Tensor]:
    """score -> ``[layer, head]``: the mean over (sequence, query) pairs."""
    cfg = model.cfg
    queries = score_queries(half_len)
    sums = {k: torch.zeros(cfg.n_layers, cfg.n_heads, dtype=torch.float64) for k in queries}
    for b0 in range(0, toks.shape[0], batch_size):
        batch = toks[b0:b0 + batch_size].to(cfg.device)
        _, cache = model.run_with_cache(batch, names_filter=lambda n: n.endswith("attn.hook_pattern"))
        for l in range(cfg.n_layers):
            for k, v in pattern_score_sums(cache[f"blocks.{l}.attn.hook_pattern"], half_len, start).items():
                sums[k][l] += v.double().cpu()
        del cache
    return {k: (sums[k] / (toks.shape[0] * len(queries[k][0]))).float() for k in sums}


@torch.no_grad()
def copy_scores(model, toks: Tensor, half_len: int, start: int, batch_size: int) -> Tensor:
    """``[layer, head]``: the mean over sequences and second-half positions j
    = S..2S-2 of ``<z_j W_O, W_U[:, x_{j+1}]>``, the head's write to the
    residual stream dotted with the unembedding of the token it should
    predict. No ``b_O`` (it is per layer, not per head) and no final LayerNorm
    (wang-2022 fn. 1). The last position is excluded: it has no next token."""
    cfg = model.cfg
    S = half_len
    qs = torch.tensor([start + j for j in range(S, 2 * S - 1)], device=cfg.device)
    total = torch.zeros(cfg.n_layers, cfg.n_heads, dtype=torch.float64)
    for b0 in range(0, toks.shape[0], batch_size):
        batch = toks[b0:b0 + batch_size].to(cfg.device)
        _, cache = model.run_with_cache(batch, names_filter=lambda n: n.endswith("attn.hook_z"))
        w_u = model.W_U[:, batch[:, qs + 1]].permute(1, 2, 0)  # [b, q, d_model]
        for l in range(cfg.n_layers):
            z = cache[f"blocks.{l}.attn.hook_z"][:, qs]  # [b, q, head, d_head]
            out = torch.einsum("bqhd,hdm->bqhm", z, model.W_O[l])
            total[l] += torch.einsum("bqhm,bqm->h", out, w_u).double().cpu()
        del cache
    return (total / (toks.shape[0] * len(qs))).float()
