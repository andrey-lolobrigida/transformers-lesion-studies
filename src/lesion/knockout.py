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
