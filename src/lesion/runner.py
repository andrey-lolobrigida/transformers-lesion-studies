"""Drives one run: pairs -> grouped batches -> clean and intervened passes ->
per-prompt metrics -> aggregates. The Python API E3's sweep script will call;
the CLI is a thin wrapper (ablate.py)."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

import torch
from torch import Tensor

from src.lesion.interventions import (
    position_mask, run_intervened, run_with_pattern_cache, sender_cache, zero_value,
)
from src.lesion.spec import AblationSpec, Head, Inputs, SpecError

COLUMNS = ("ld_clean", "ld_ablated", "p_c_clean", "p_c_ablated", "c_over_s_clean", "c_over_s_ablated")


@dataclass
class RunResult:
    spec: AblationSpec
    n: int
    seed: int
    prepend_bos: bool
    batch_size: int
    destination: str  # "clean" or "corrupt": which prompt the intervention ran on
    columns: dict[str, Tensor]  # COLUMNS -> float32 [n], prompt order
    templates: list[str]
    meta: dict[str, list[str]]  # battery meta, column-wise
    aggregates: dict
    reference_summary: dict | None
    seconds: float


def group_by_length(id_lists, batch_size: int) -> list[list[int]]:
    """Batches of indices whose token sequences share a length, so no padding or
    attention mask exists (E0's trick). Lengths ascending, index order within a
    length, then chunks of ``batch_size``. Identical to E0's iteration order."""
    groups: dict[int, list[int]] = defaultdict(list)
    for i, ids in enumerate(id_lists):
        groups[len(ids)].append(i)
    batches = []
    for length in sorted(groups):
        idxs = groups[length]
        for start in range(0, len(idxs), batch_size):
            batches.append(idxs[start:start + batch_size])
    return batches


def metrics(logits: Tensor, end_idx: Tensor, answer_ids: Tensor, competitor_ids: Tensor) -> tuple[Tensor, Tensor, Tensor]:
    """Per prompt at END: logit difference c - s, P[c], 1[logit c > logit s].
    Expressions match E0's step_ioi exactly (bitwise parity is a slow-tier check)."""
    final = logits[torch.arange(logits.shape[0], device=logits.device), end_idx, :].float()
    c = final.gather(1, answer_ids[:, None])[:, 0]
    s = final.gather(1, competitor_ids[:, None])[:, 0]
    probs = final.log_softmax(-1).exp()
    ld = c - s
    p_c = probs.gather(1, answer_ids[:, None])[:, 0]
    return ld.cpu(), p_c.cpu(), (ld > 0).float().cpu()


def _side(t: dict[str, Tensor], suffix: str, n: int) -> dict:
    ld = t["ld_" + suffix]
    return {
        "n": n,
        "mean_ld": ld.mean().item(), "std_ld": ld.std().item(), "sem_ld": (ld.std() / n ** 0.5).item(),
        "mean_p_c": t["p_c_" + suffix].mean().item(), "c_over_s": t["c_over_s_" + suffix].mean().item(),
    }


def _effect(t: dict[str, Tensor], name: str, n: int, ratios: bool) -> dict:
    c, a = t[f"{name}_clean"], t[f"{name}_ablated"]
    d = c - a  # positive: the ablation hurt (docs/01-methods.md, effect sizes)
    out = {"effect_mean": d.mean().item(), "sem": (d.std() / n ** 0.5).item()}
    if ratios:
        r = a / c
        q = torch.quantile(r, torch.tensor([0.25, 0.75]))
        out.update({
            "ratio_of_means": (a.mean() / c.mean()).item(),
            "mean_of_ratios": r.mean().item(),
            "ratio_iqr": [q[0].item(), q[1].item()],
            "n_abs_clean_below_0.1": int((c.abs() < 0.1).sum()),
        })
    return out


def aggregate(columns: dict[str, Tensor], templates: list[str]) -> dict:
    n = len(templates)
    t = {k: v.float() for k, v in columns.items()}
    by_template = {}
    for tmpl in sorted(set(templates)):
        mask = torch.tensor([x == tmpl for x in templates])
        by_template[tmpl] = {
            "n": int(mask.sum()),
            "clean": {"mean_ld": t["ld_clean"][mask].mean().item(), "mean_p_c": t["p_c_clean"][mask].mean().item(),
                      "c_over_s": t["c_over_s_clean"][mask].mean().item()},
            "ablated": {"mean_ld": t["ld_ablated"][mask].mean().item(), "mean_p_c": t["p_c_ablated"][mask].mean().item(),
                        "c_over_s": t["c_over_s_ablated"][mask].mean().item()},
        }
    return {
        "clean": _side(t, "clean", n),
        "ablated": _side(t, "ablated", n),
        "effect": {"ld": _effect(t, "ld", n, True), "p_c": _effect(t, "p_c", n, False),
                   "c_over_s": _effect(t, "c_over_s", n, False)},
        "by_template": by_template,
    }


def _check_bounds(spec: AblationSpec, cfg, labels: tuple[str, ...]) -> None:
    c = spec.component
    if c.layer >= cfg.n_layers:
        raise SpecError(f"layer {c.layer} out of range for {cfg.n_layers} layers")
    if isinstance(c, Head) and c.head >= cfg.n_heads:
        raise SpecError(f"head {c.head} out of range for {cfg.n_heads} heads")
    if isinstance(spec.receiver, Inputs):
        for layer, head, _, label in spec.receiver.targets:
            if layer >= cfg.n_layers or head >= cfg.n_heads:
                raise SpecError(f"receiver target L{layer}H{head} out of range")
            if label not in labels:
                raise SpecError(f"unknown position label {label!r}; battery has {labels}")
    if hasattr(spec.positions, "labels"):
        for label in spec.positions.labels:
            if label not in labels:
                raise SpecError(f"unknown position label {label!r}; battery has {labels}")


@torch.no_grad()
def run(model, spec: AblationSpec, battery, n: int, seed: int, prepend_bos: bool, batch_size: int) -> RunResult:
    from src.lesion.reference import compute_mean_reference

    t0 = time.time()
    _check_bounds(spec, model.cfg, tuple(battery.labels))
    pairs = battery.pairs(n, seed, prepend_bos)  # alignment failures raise here
    if spec.direction == "ablate-clean":
        dst = [p.clean_ids for p in pairs]
        src = [p.corrupt_ids for p in pairs]
        labels = [p.positions for p in pairs]
        destination = "clean"
    else:
        dst = [p.corrupt_ids for p in pairs]
        src = [p.clean_ids for p in pairs]
        labels = [p.corrupt_positions for p in pairs]
        destination = "corrupt"
    reference = None
    if spec.value == "mean":
        reference = compute_mean_reference(model, spec.reference, spec.component, battery, prepend_bos, batch_size)

    device = model.cfg.device
    columns = {k: torch.empty(n, dtype=torch.float32) for k in COLUMNS}
    for batch in group_by_length(dst, batch_size):
        dst_toks = torch.tensor([dst[i] for i in batch], device=device)
        seq_len = dst_toks.shape[1]
        batch_labels = [labels[i] for i in batch]
        end = torch.tensor([labels[i]["END"] for i in batch], device=device)
        ans = torch.tensor([pairs[i].answer_id for i in batch], device=device)
        comp = torch.tensor([pairs[i].competitor_id for i in batch], device=device)

        if spec.freeze_patterns:
            base, patterns = run_with_pattern_cache(model, dst_toks)
        else:
            base, patterns = model(dst_toks), None  # the plain call E0 made

        mask = position_mask(spec.positions, batch_labels, seq_len, device)
        if spec.value == "zero":
            v = zero_value(spec.component, len(batch), seq_len, model.cfg, device, base.dtype)
        elif spec.value == "resample":
            v = sender_cache(model, torch.tensor([src[i] for i in batch], device=device), spec.component)
        else:
            v = reference.value_for([pairs[i].template for i in batch], seq_len).to(device=device, dtype=base.dtype)
        out = run_intervened(model, spec, dst_toks, mask, v, batch_labels, patterns)

        idx = torch.tensor(batch)
        for name, logits in (("clean", base), ("ablated", out)):
            ld, p_c, cs = metrics(logits, end, ans, comp)
            columns[f"ld_{name}"][idx] = ld
            columns[f"p_c_{name}"][idx] = p_c
            columns[f"c_over_s_{name}"][idx] = cs

    templates = [p.template for p in pairs]
    meta_keys = sorted({k for p in pairs for k in p.meta})
    meta = {k: [str(p.meta.get(k, "")) for p in pairs] for k in meta_keys}
    return RunResult(
        spec=spec, n=n, seed=seed, prepend_bos=prepend_bos, batch_size=batch_size, destination=destination,
        columns=columns, templates=templates, meta=meta, aggregates=aggregate(columns, templates),
        reference_summary=None if reference is None else reference.summary(), seconds=time.time() - t0,
    )
