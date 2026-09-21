"""Mean references, computed per run from a seeded draw and never cached to
disk (spec, decision 3). The result carries n, seed, match, battery side and
the per-template counts, so every mean-ablation number can log its reference
size (CLAUDE.md, epistemic rule 4)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import torch
from torch import Tensor

from src.lesion.interventions import component_slice, hook_name
from src.lesion.spec import Component, MeanReference


class ReferenceError(ValueError):
    """A destination prompt has no usable reference. A hard stop."""


@dataclass
class MeanReferenceValues:
    spec: MeanReference
    component: Component
    per_template: dict[str, Tensor] | None  # template -> [pos, d]   (match == "template")
    pooled: Tensor | None  # [d]                                   (match == "pooled")
    counts: dict[str, int]  # prompts per template in the reference draw
    n_prompts: int

    def value_for(self, templates: list[str], seq_len: int) -> Tensor:
        """The substitution tensor for a batch: ``[batch, seq_len, d]``."""
        if self.spec.match == "pooled":
            assert self.pooled is not None
            return self.pooled.expand(len(templates), seq_len, -1).clone()
        assert self.per_template is not None
        rows = []
        for t in templates:
            if t not in self.per_template:
                raise ReferenceError(
                    f"no reference prompts for template {t!r} in a draw of {self.n_prompts} "
                    f"(counts: {self.counts}); raise the reference n")
            ref = self.per_template[t]
            if ref.shape[0] != seq_len:
                raise ReferenceError(f"template {t!r}: reference has {ref.shape[0]} positions, batch has {seq_len}")
            rows.append(ref)
        return torch.stack(rows)

    def summary(self) -> dict:
        return {
            "battery_side": self.spec.battery_side, "n": self.spec.n, "seed": self.spec.seed,
            "match": self.spec.match, "n_prompts_used": self.n_prompts,
            "per_template_counts": dict(sorted(self.counts.items())), "hook": hook_name(self.component),
        }


@torch.no_grad()
def compute_mean_reference(model, ref: MeanReference, component: Component, battery, prepend_bos: bool,
                           batch_size: int) -> MeanReferenceValues:
    from src.lesion.runner import group_by_length  # local import: runner imports this module

    pairs = battery.pairs(ref.n, ref.seed, prepend_bos)
    ids = [p.clean_ids if ref.battery_side == "clean" else p.corrupt_ids for p in pairs]
    device = model.cfg.device
    name = hook_name(component)
    sums: dict[str, Tensor] = {}
    counts: dict[str, int] = defaultdict(int)
    pooled_sum: Tensor | None = None
    pooled_count = 0
    for batch in group_by_length(ids, batch_size):
        toks = torch.tensor([ids[i] for i in batch], device=device)
        _, cache = model.run_with_cache(toks, names_filter=lambda n: n == name)
        acts = component_slice(cache[name], component).float()  # [b, pos, d]
        for j, i in enumerate(batch):  # one row at a time: batch-size invariant
            row = acts[j]
            t = pairs[i].template
            if t in sums:
                sums[t] = sums[t] + row
            else:
                sums[t] = row.clone()
            counts[t] += 1
            for pos_row in row:
                pooled_sum = pos_row.clone() if pooled_sum is None else pooled_sum + pos_row
                pooled_count += 1
    if ref.match == "template":
        per_template = {t: sums[t] / counts[t] for t in sums}
        return MeanReferenceValues(ref, component, per_template, None, dict(counts), len(pairs))
    assert pooled_sum is not None
    return MeanReferenceValues(ref, component, None, pooled_sum / pooled_count, dict(counts), len(pairs))
