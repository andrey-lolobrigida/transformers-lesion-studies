"""Set knockout (E2): several heads knocked out together, each at its own
positions, or everything *except* such a set (``complement``: Wang et al.'s
circuit knockout, C(x) = the model with every node outside C knocked out,
wang-2022 §2.1). Built from the primitives in ``interventions.py``;
``interventions.py``, ``runner.py``, ``reference.py`` and ``spec.py`` are
untouched (D-015 item 8; a forced generalisation under D-014 item 6).

A member is a (head, positions) pair: Wang's unit is the (head, token
position) node, so a circuit head is kept only at its class's position and
knocked out everywhere else (O-013). Heads only (``granularity: "heads"``):
MLPs are never knocked out here, as Wang leaves them in the direct path
(wang-2022 §3). Template-matched means only (O-013). ``complement`` is
defined for ablate-clean only."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Mapping

import torch
from torch import Tensor

from src.lesion.interventions import freeze_hooks, position_mask, run_with_pattern_cache
from src.lesion.reference import ReferenceError
from src.lesion.runner import COLUMNS, RunResult, aggregate, group_by_length, metrics
from src.lesion.spec import AblationSpec, All, Head, Labels, MeanReference, Positions, SpecError


@dataclass(frozen=True)
class Member:
    head: Head
    positions: Positions


def positions_json(p: Positions) -> dict:
    if isinstance(p, All):
        return {"kind": "all"}
    if isinstance(p, Labels):
        return {"kind": "labels", "labels": list(p.labels)}
    return {"kind": "indices", "indices": list(p.indices)}


@dataclass(frozen=True)
class KnockoutSetSpec:
    members: tuple[Member, ...]
    complement: bool  # False: knock out the members at their positions; True: everything else
    value: Literal["zero", "mean", "resample"]
    reference: MeanReference | None  # required iff value == "mean"; template-matched only
    direction: Literal["ablate-clean", "restore-clean"]
    freeze_patterns: bool
    granularity: Literal["heads"]

    def __post_init__(self) -> None:
        if self.granularity != "heads":
            raise SpecError(f"granularity must be 'heads', got {self.granularity!r}")
        if not isinstance(self.members, tuple):
            raise SpecError("members must be a tuple of Member")
        seen: set[Head] = set()
        for m in self.members:
            if not isinstance(m, Member) or not isinstance(m.head, Head):
                raise SpecError(f"a member is Member(Head, positions); got {m!r}")
            if m.head in seen:
                raise SpecError(f"duplicate member {m.head!r}")
            seen.add(m.head)
            # The single-component rules for a head and its positions, reused verbatim.
            AblationSpec(component=m.head, value="zero", reference=None, component_type="node", receiver=None,
                         mlp_convention=None, positions=m.positions, direction="ablate-clean", freeze_patterns=False)
        # The single-component rules for value, reference and direction, on a stand-in head.
        AblationSpec(component=Head(0, 0), value=self.value, reference=self.reference, component_type="node",
                     receiver=None, mlp_convention=None, positions=All(), direction=self.direction,
                     freeze_patterns=self.freeze_patterns)
        if self.reference is not None and self.reference.match != "template":
            raise SpecError("set knockout uses template-matched means only (O-013)")
        if self.complement and self.direction != "ablate-clean":
            raise SpecError("complement is defined for ablate-clean only (Wang's circuit knockout)")

    @property
    def direct_effect_definition(self) -> None:
        return None  # node knockout; recorded as null next to every set number

    def layers(self, n_layers: int) -> tuple[int, ...]:
        """Every layer whose hook_z this spec can write."""
        if self.complement:
            return tuple(range(n_layers))
        return tuple(sorted({m.head.layer for m in self.members}))

    def to_json(self) -> dict:
        r = self.reference
        return {
            "granularity": self.granularity,
            "component_type": "node",
            "value": self.value,
            "reference": None if r is None else {"battery_side": r.battery_side, "n": r.n, "seed": r.seed,
                                                 "match": r.match},
            "direction": self.direction,
            "freeze_patterns": self.freeze_patterns,
            "set": {"complement": self.complement,
                    "members": [{"head": {"layer": m.head.layer, "head": m.head.head},
                                 "positions": positions_json(m.positions)} for m in self.members]},
        }


def check_bounds(spec: KnockoutSetSpec, cfg, labels: tuple[str, ...]) -> None:
    for m in spec.members:
        if m.head.layer >= cfg.n_layers or m.head.head >= cfg.n_heads:
            raise SpecError(f"member {m.head!r} out of range for {cfg.n_layers} layers x {cfg.n_heads} heads")
        if isinstance(m.positions, Labels):
            for label in m.positions.labels:
                if label not in labels:
                    raise SpecError(f"unknown position label {label!r}; battery has {labels}")


def layer_masks(spec: KnockoutSetSpec, n_layers: int, n_heads: int, per_prompt_labels: list[Mapping[str, int]],
                seq_len: int, device) -> dict[int, Tensor]:
    """layer -> bool ``[batch, pos, head]``: where the substitution is written.
    Layers with nothing to write are omitted."""
    batch = len(per_prompt_labels)
    per_layer: dict[int, Tensor] = {}
    if spec.complement:
        per_layer = {l: torch.ones(batch, seq_len, n_heads, dtype=torch.bool, device=device) for l in range(n_layers)}
    for m in spec.members:
        pm = position_mask(m.positions, per_prompt_labels, seq_len, device)  # [batch, pos]
        layer, head = m.head.layer, m.head.head
        if spec.complement:
            per_layer[layer][:, :, head] &= ~pm
        else:
            if layer not in per_layer:
                per_layer[layer] = torch.zeros(batch, seq_len, n_heads, dtype=torch.bool, device=device)
            per_layer[layer][:, :, head] |= pm
    return {l: mask for l, mask in sorted(per_layer.items()) if bool(mask.any())}


# --- mean reference over many heads ---------------------------------------------


@dataclass
class SetMeanReference:
    """Template-matched means of every head in ``layers``, from one caching
    pass. Per head it equals ``reference.compute_mean_reference`` bitwise:
    same batches, same row-by-row float32 sums, same division."""

    spec: MeanReference
    layers: tuple[int, ...]
    per_template: dict[str, dict[int, Tensor]]  # template -> layer -> [pos, head, d_head]
    counts: dict[str, int]
    n_prompts: int

    def value_for(self, layer: int, templates: list[str], seq_len: int) -> Tensor:
        """The substitution tensor for one layer of a batch: ``[batch, seq_len, head, d_head]``."""
        rows = []
        for t in templates:
            if t not in self.per_template:
                raise ReferenceError(
                    f"no reference prompts for template {t!r} in a draw of {self.n_prompts} "
                    f"(counts: {self.counts}); raise the reference n")
            ref = self.per_template[t][layer]
            if ref.shape[0] != seq_len:
                raise ReferenceError(f"template {t!r}: reference has {ref.shape[0]} positions, batch has {seq_len}")
            rows.append(ref)
        return torch.stack(rows)

    def summary(self) -> dict:
        return {
            "battery_side": self.spec.battery_side, "n": self.spec.n, "seed": self.spec.seed,
            "match": self.spec.match, "n_prompts_used": self.n_prompts,
            "per_template_counts": dict(sorted(self.counts.items())),
            "hook": [f"blocks.{l}.attn.hook_z" for l in self.layers],
        }


@torch.no_grad()
def compute_set_mean_reference(model, ref: MeanReference, layers: tuple[int, ...], battery, prepend_bos: bool,
                               batch_size: int) -> SetMeanReference:
    pairs = battery.pairs(ref.n, ref.seed, prepend_bos)
    ids = [p.clean_ids if ref.battery_side == "clean" else p.corrupt_ids for p in pairs]
    names = {f"blocks.{l}.attn.hook_z": l for l in layers}
    sums: dict[str, dict[int, Tensor]] = {}
    counts: dict[str, int] = defaultdict(int)
    for batch in group_by_length(ids, batch_size):
        toks = torch.tensor([ids[i] for i in batch], device=model.cfg.device)
        _, cache = model.run_with_cache(toks, names_filter=lambda n: n in names)
        acts = {l: cache[name].float() for name, l in names.items()}  # [b, pos, head, d_head]
        for j, i in enumerate(batch):  # one row at a time, as reference.py: batch-size invariant
            t = pairs[i].template
            if t in sums:
                for l in layers:
                    sums[t][l] = sums[t][l] + acts[l][j]
            else:
                sums[t] = {l: acts[l][j].clone() for l in layers}
            counts[t] += 1
    per_template = {t: {l: s / counts[t] for l, s in d.items()} for t, d in sums.items()}
    return SetMeanReference(ref, tuple(layers), per_template, dict(counts), len(pairs))


# --- running ------------------------------------------------------------------------


def _writer(mask: Tensor, v: Tensor):
    def fn(x, hook):
        x = x.clone()
        x[mask] = v[mask]
        return x

    return fn


@torch.no_grad()
def run_set(model, spec: KnockoutSetSpec, battery, n: int, seed: int, prepend_bos: bool, batch_size: int) -> RunResult:
    """``runner.run`` for a set: same pairs, batches, clean pass, metrics and
    aggregates, so a one-member set equals the single node run bitwise. The
    returned ``RunResult.spec`` is the ``KnockoutSetSpec``."""
    t0 = time.time()
    cfg = model.cfg
    check_bounds(spec, cfg, tuple(battery.labels))
    pairs = battery.pairs(n, seed, prepend_bos)
    if spec.direction == "ablate-clean":
        dst, src = [p.clean_ids for p in pairs], [p.corrupt_ids for p in pairs]
        labels, destination = [p.positions for p in pairs], "clean"
    else:
        dst, src = [p.corrupt_ids for p in pairs], [p.clean_ids for p in pairs]
        labels, destination = [p.corrupt_positions for p in pairs], "corrupt"
    reference = None
    if spec.value == "mean":
        reference = compute_set_mean_reference(model, spec.reference, spec.layers(cfg.n_layers), battery,
                                               prepend_bos, batch_size)

    device = cfg.device
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
            base, patterns = model(dst_toks), None

        masks = layer_masks(spec, cfg.n_layers, cfg.n_heads, batch_labels, seq_len, device)
        src_cache = None
        if spec.value == "resample" and masks:
            wanted = {f"blocks.{l}.attn.hook_z" for l in masks}
            _, src_cache = model.run_with_cache(torch.tensor([src[i] for i in batch], device=device),
                                                names_filter=lambda nm: nm in wanted)
        hooks = []
        for layer, mask in masks.items():
            name = f"blocks.{layer}.attn.hook_z"
            if spec.value == "zero":
                v = torch.zeros(len(batch), seq_len, cfg.n_heads, cfg.d_head, device=device, dtype=base.dtype)
            elif spec.value == "resample":
                v = src_cache[name]
            else:
                v = reference.value_for(layer, [pairs[i].template for i in batch], seq_len).to(
                    device=device, dtype=base.dtype)
            hooks.append((name, _writer(mask, v)))
        if patterns is not None:
            hooks += freeze_hooks(patterns)
        out = model.run_with_hooks(dst_toks, fwd_hooks=hooks)

        idx = torch.tensor(batch)
        for name, logits in (("clean", base), ("ablated", out)):
            ld, p_c, cs = metrics(logits, end, ans, comp)
            columns[f"ld_{name}"][idx] = ld
            columns[f"p_c_{name}"][idx] = p_c
            columns[f"c_over_s_{name}"][idx] = cs
        del base, out, logits, src_cache  # frees memory only (see runner.run)

    templates = [p.template for p in pairs]
    meta_keys = sorted({k for p in pairs for k in p.meta})
    meta = {k: [str(p.meta.get(k, "")) for p in pairs] for k in meta_keys}
    return RunResult(
        spec=spec, n=n, seed=seed, prepend_bos=prepend_bos, batch_size=batch_size, destination=destination,
        columns=columns, templates=templates, meta=meta, aggregates=aggregate(columns, templates),
        reference_summary=None if reference is None else reference.summary(), seconds=time.time() - t0,
    )
