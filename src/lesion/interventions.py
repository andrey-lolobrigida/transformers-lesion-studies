"""From (spec, substitution tensor) to TransformerLens hooks.

Pure with respect to the battery and the reference: the caller builds the
substitution value ``v`` (zeros, a mean, or a source-run activation) and the
boolean position mask; this module only decides where to write it and how the
downstream computation is constrained (node / freeze / edge). E1b and E3
should never need to edit this file; if they do, record it as a design
failure (spec, "Modules").

Hook points used (transformer_lens 3.9.0):
  blocks.{L}.attn.hook_z        [batch, pos, head, d_head]   head output before W_O
  blocks.{L}.hook_mlp_out       [batch, pos, d_model]
  blocks.{L}.attn.hook_pattern  [batch, head, q_pos, k_pos]
  blocks.{L}.attn.hook_{q,k,v}  [batch, pos, head, d_head]
  blocks.{L_last}.hook_resid_post [batch, pos, d_model]
"""

from __future__ import annotations

from typing import Callable, Mapping

import torch
from torch import Tensor

from src.lesion.spec import MLP, AblationSpec, All, Component, Head, Labels, Logits, Positions, SpecError

Hook = tuple[str, Callable]


# --- names and slices ---------------------------------------------------------


def hook_name(component: Component) -> str:
    if isinstance(component, Head):
        return f"blocks.{component.layer}.attn.hook_z"
    return f"blocks.{component.layer}.hook_mlp_out"


def component_slice(x: Tensor, component: Component) -> Tensor:
    """The component's own activation: ``[batch, pos, d]``."""
    return x[:, :, component.head, :] if isinstance(component, Head) else x


def n_layers(model) -> int:
    return model.cfg.n_layers


# --- positions -----------------------------------------------------------------


def resolve_label(labels: Mapping[str, int], label: str) -> int:
    try:
        return labels[label]
    except KeyError:
        raise SpecError(f"unknown position label {label!r}; this prompt has {sorted(labels)}") from None


def position_mask(positions: Positions, per_prompt_labels: list[Mapping[str, int]], seq_len: int, device) -> Tensor:
    """Boolean ``[batch, pos]``: where the substitution is written."""
    batch = len(per_prompt_labels)
    mask = torch.zeros(batch, seq_len, dtype=torch.bool, device=device)
    if isinstance(positions, All):
        mask[:] = True
    elif isinstance(positions, Labels):
        for b, labels in enumerate(per_prompt_labels):
            for label in positions.labels:
                mask[b, resolve_label(labels, label)] = True
    else:
        for i in positions.indices:
            if i >= seq_len:
                raise SpecError(f"position index {i} out of range for sequence length {seq_len}")
            mask[:, i] = True
    return mask


# --- substitution ---------------------------------------------------------------


def substitute(x: Tensor, mask: Tensor, v: Tensor, head: int | None) -> Tensor:
    """``x`` with ``v`` written at the masked positions (of one head, if given).
    Never modifies ``x``."""
    x = x.clone()
    if head is None:
        x[mask] = v[mask]
    else:
        x[:, :, head, :][mask] = v[mask]  # basic-index view; advanced assignment writes through
    return x


def node_hooks(component: Component, mask: Tensor, v: Tensor) -> list[Hook]:
    head = component.head if isinstance(component, Head) else None

    def fn(x, hook):
        return substitute(x, mask, v, head)

    return [(hook_name(component), fn)]


def zero_value(component: Component, batch: int, seq_len: int, cfg, device, dtype) -> Tensor:
    d = cfg.d_head if isinstance(component, Head) else cfg.d_model
    return torch.zeros(batch, seq_len, d, device=device, dtype=dtype)


@torch.no_grad()
def sender_cache(model, toks: Tensor, component: Component) -> Tensor:
    """The component's activation on ``toks``: the resample value when ``toks``
    is the source prompt, and pass A of the edge routine."""
    name = hook_name(component)
    _, cache = model.run_with_cache(toks, names_filter=lambda n: n == name)
    return component_slice(cache[name], component)


# --- pattern freezing (node only) ---------------------------------------------------


@torch.no_grad()
def run_with_pattern_cache(model, toks: Tensor) -> tuple[Tensor, dict[str, Tensor]]:
    """Logits plus every layer's attention pattern from the same (destination)
    run; the pattern cache is what freezing pins (Olsson et al.: patterns from
    the unablated run of the same input)."""
    logits, cache = model.run_with_cache(toks, names_filter=lambda n: n.endswith("attn.hook_pattern"))
    return logits, {name: cache[name] for name in cache.keys()}


def freeze_hooks(patterns: dict[str, Tensor]) -> list[Hook]:
    def fn(x, hook):
        return patterns[hook.name]

    return [(name, fn) for name in sorted(patterns)]


# --- running -----------------------------------------------------------------------


@torch.no_grad()
def run_node(model, spec: AblationSpec, dst_toks: Tensor, mask: Tensor, v: Tensor,
             patterns: dict[str, Tensor] | None = None) -> Tensor:
    hooks = node_hooks(spec.component, mask, v)
    if spec.freeze_patterns:
        if patterns is None:
            raise ValueError("freeze_patterns needs the destination run's pattern cache")
        hooks += freeze_hooks(patterns)
    return model.run_with_hooks(dst_toks, fwd_hooks=hooks)


@torch.no_grad()
def run_edge(model, spec: AblationSpec, dst_toks: Tensor, mask: Tensor, v: Tensor,
             dst_labels: list[Mapping[str, int]]) -> Tensor:
    """Wang et al. Algorithm 1 as passes B, C, D on the destination prompt.
    Pass A (the source activation) is the caller's ``v`` for resample; for zero
    and mean ``v`` is the substitution value directly (Miller et al. App. F:
    the same routine is edge zero / edge mean ablation)."""
    L = n_layers(model)
    last = L - 1
    sender = hook_name(spec.component)
    sender_head = spec.component.head if isinstance(spec.component, Head) else None
    z_names = [f"blocks.{l}.attn.hook_z" for l in range(L)]
    mlp_names = [f"blocks.{l}.hook_mlp_out" for l in range(L)]
    if isinstance(spec.receiver, Logits):
        receiver_names = [f"blocks.{last}.hook_resid_post"]
        targets_by_hook: dict[str, list[tuple[int, str]]] = {}
    else:
        targets_by_hook = {}
        for layer, head, inp, label in spec.receiver.targets:
            if layer >= L:
                raise SpecError(f"receiver target layer {layer} beyond the model's {L} layers")
            targets_by_hook.setdefault(f"blocks.{layer}.attn.hook_{inp}", []).append((head, label))
        receiver_names = sorted(targets_by_hook)

    # B: the unintervened destination run, everything we will pin or compare.
    wanted = set(z_names) | set(mlp_names) | set(receiver_names)
    _, B = model.run_with_cache(dst_toks, names_filter=lambda n: n in wanted)

    # C: pin every head (and, under term, every MLP) to B; the sender gets v.
    def pin(x, hook):
        return B[hook.name]

    def sender_fn(x, hook):
        return substitute(B[hook.name], mask, v, sender_head)

    hooks: list[Hook] = []
    for name in z_names:
        hooks.append((name, sender_fn if name == sender else pin))
    for name in mlp_names:
        if name == sender:
            hooks.append((name, sender_fn))
        elif spec.mlp_convention == "term":
            hooks.append((name, pin))
    captured: dict[str, Tensor] = {}

    def capture(x, hook):
        captured[hook.name] = x.clone()
        return x

    hooks += [(name, capture) for name in receiver_names]
    model.run_with_hooks(dst_toks, fwd_hooks=hooks)

    # D: only the receivers take their C values; everything else recomputes.
    if isinstance(spec.receiver, Logits):
        def take_c(x, hook):
            return captured[hook.name]

        d_hooks: list[Hook] = [(receiver_names[0], take_c)]
    else:
        def make(targets: list[tuple[int, str]]):
            def fn(x, hook):
                x = x.clone()
                c = captured[hook.name]
                for head, label in targets:
                    for b, labels in enumerate(dst_labels):
                        p = resolve_label(labels, label)
                        x[b, p, head, :] = c[b, p, head, :]
                return x

            return fn

        d_hooks = [(name, make(targets)) for name, targets in targets_by_hook.items()]
    return model.run_with_hooks(dst_toks, fwd_hooks=d_hooks)


@torch.no_grad()
def run_intervened(model, spec: AblationSpec, dst_toks: Tensor, mask: Tensor, v: Tensor,
                   dst_labels: list[Mapping[str, int]], patterns: dict[str, Tensor] | None = None) -> Tensor:
    """Logits of the destination prompt under the spec's intervention."""
    if spec.component_type == "node":
        return run_node(model, spec, dst_toks, mask, v, patterns)
    return run_edge(model, spec, dst_toks, mask, v, dst_labels)
