"""The run specification. Every axis of Miller et al.'s six-tuple (granularity,
component type, substitution value, positions, direction, component set) plus
this project's pattern-freezing axis and the MLP convention is an explicit
field. There are no defaults here; convenience defaults live in the CLI and
are written to the artifact (O-011 rule: a default that goes unstated becomes
a permanent choice nobody made)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

VALUES = ("zero", "mean", "resample")
DIRECTIONS = ("ablate-clean", "restore-clean")
CONVENTIONS = ("wang", "term")
INPUTS = ("q", "k", "v")


class SpecError(ValueError):
    """An ill-formed specification. Raised before any model loads."""


@dataclass(frozen=True)
class Head:
    layer: int
    head: int


@dataclass(frozen=True)
class MLP:
    layer: int


Component = Union[Head, MLP]


@dataclass(frozen=True)
class MeanReference:
    battery_side: Literal["clean", "corrupt"]  # which distribution the mean is over
    n: int
    seed: int
    match: Literal["template", "pooled"]


@dataclass(frozen=True)
class Logits:
    """Edge receiver: the final residual stream, i.e. the logits."""


@dataclass(frozen=True)
class Inputs:
    """Edge receiver: named q/k/v inputs of later heads at a position label."""

    targets: tuple[tuple[int, int, Literal["q", "k", "v"], str], ...]  # (layer, head, input, label)


Receiver = Union[Logits, Inputs]


@dataclass(frozen=True)
class All:
    pass


@dataclass(frozen=True)
class Labels:
    labels: tuple[str, ...]


@dataclass(frozen=True)
class Indices:
    indices: tuple[int, ...]


Positions = Union[All, Labels, Indices]


@dataclass(frozen=True)
class AblationSpec:
    component: Component
    value: Literal["zero", "mean", "resample"]
    reference: MeanReference | None  # required iff value == "mean"
    component_type: Literal["node", "edge"]
    receiver: Receiver | None  # required iff edge
    mlp_convention: Literal["wang", "term"] | None  # required iff edge
    positions: Positions
    direction: Literal["ablate-clean", "restore-clean"]
    freeze_patterns: bool

    def __post_init__(self) -> None:
        if not isinstance(self.component, (Head, MLP)):
            raise SpecError(f"component must be Head or MLP, got {self.component!r}")
        if self.component.layer < 0 or (isinstance(self.component, Head) and self.component.head < 0):
            raise SpecError(f"negative layer or head in {self.component!r}")
        if self.value not in VALUES:
            raise SpecError(f"value must be one of {VALUES}, got {self.value!r}")
        if self.direction not in DIRECTIONS:
            raise SpecError(f"direction must be one of {DIRECTIONS}, got {self.direction!r}")
        if self.component_type not in ("node", "edge"):
            raise SpecError(f"component_type must be 'node' or 'edge', got {self.component_type!r}")
        if (self.value == "mean") != (self.reference is not None):
            raise SpecError("a MeanReference is required exactly when value == 'mean'")
        if self.reference is not None:
            r = self.reference
            if r.battery_side not in ("clean", "corrupt") or r.match not in ("template", "pooled"):
                raise SpecError(f"bad MeanReference {r!r}")
            if r.n <= 0:
                raise SpecError("mean reference size must be positive")
        if self.component_type == "edge":
            if self.freeze_patterns:
                raise SpecError("freeze_patterns with edge ablation is refused, not defined (spec, decision 4)")
            if self.receiver is None:
                raise SpecError("edge ablation needs a receiver (Logits or Inputs)")
            if self.mlp_convention not in CONVENTIONS:
                raise SpecError(f"edge ablation needs mlp_convention in {CONVENTIONS}")
            if isinstance(self.receiver, Inputs):
                if not self.receiver.targets:
                    raise SpecError("Inputs receiver needs at least one target")
                for layer, head, inp, label in self.receiver.targets:
                    if layer <= self.component.layer:
                        raise SpecError(
                            f"receiver target layer {layer} is at or below the sender's layer "
                            f"{self.component.layer}: the path would be empty")
                    if head < 0 or inp not in INPUTS or not isinstance(label, str) or not label:
                        raise SpecError(f"bad receiver target {(layer, head, inp, label)!r}")
        else:
            if self.receiver is not None or self.mlp_convention is not None:
                raise SpecError("receiver and mlp_convention are edge-only fields")
        p = self.positions
        if isinstance(p, Labels):
            if not p.labels or not all(isinstance(x, str) and x for x in p.labels):
                raise SpecError("Labels needs at least one non-empty label")
        elif isinstance(p, Indices):
            if not p.indices or any(i < 0 for i in p.indices):
                raise SpecError("Indices needs at least one non-negative index")
        elif not isinstance(p, All):
            raise SpecError(f"positions must be All, Labels or Indices, got {p!r}")

    # --- naming -------------------------------------------------------------

    def component_label(self) -> str:
        c = self.component
        return f"L{c.layer}H{c.head}" if isinstance(c, Head) else f"L{c.layer}.mlp"

    @property
    def granularity(self) -> str:
        return "head" if isinstance(self.component, Head) else "mlp-layer"

    @property
    def direct_effect_definition(self) -> str | None:
        """The project's *direct effect* is edge ablation with receiver Logits;
        the MLP convention is part of its definition (O-011)."""
        if self.component_type == "edge" and isinstance(self.receiver, Logits):
            return self.mlp_convention
        return None

    # --- JSON ---------------------------------------------------------------

    def to_json(self) -> dict:
        c = self.component
        component = ({"kind": "head", "layer": c.layer, "head": c.head} if isinstance(c, Head)
                     else {"kind": "mlp", "layer": c.layer})
        if self.receiver is None:
            receiver = None
        elif isinstance(self.receiver, Logits):
            receiver = {"kind": "logits"}
        else:
            receiver = {"kind": "inputs", "targets": [list(t) for t in self.receiver.targets]}
        p = self.positions
        positions = ({"kind": "all"} if isinstance(p, All)
                     else {"kind": "labels", "labels": list(p.labels)} if isinstance(p, Labels)
                     else {"kind": "indices", "indices": list(p.indices)})
        r = self.reference
        reference = None if r is None else {"battery_side": r.battery_side, "n": r.n, "seed": r.seed, "match": r.match}
        return {
            "granularity": self.granularity,
            "component": component,
            "component_type": self.component_type,
            "value": self.value,
            "reference": reference,
            "receiver": receiver,
            "mlp_convention": self.mlp_convention,
            "positions": positions,
            "direction": self.direction,
            "set": "single-component",
            "freeze_patterns": self.freeze_patterns,
        }

    @classmethod
    def from_json(cls, d: dict) -> "AblationSpec":
        c = d["component"]
        component = Head(c["layer"], c["head"]) if c["kind"] == "head" else MLP(c["layer"])
        r = d["receiver"]
        if r is None:
            receiver = None
        elif r["kind"] == "logits":
            receiver = Logits()
        else:
            receiver = Inputs(tuple((t[0], t[1], t[2], t[3]) for t in r["targets"]))
        p = d["positions"]
        positions = (All() if p["kind"] == "all"
                     else Labels(tuple(p["labels"])) if p["kind"] == "labels"
                     else Indices(tuple(p["indices"])))
        ref = d["reference"]
        reference = None if ref is None else MeanReference(ref["battery_side"], ref["n"], ref["seed"], ref["match"])
        return cls(component=component, value=d["value"], reference=reference,
                   component_type=d["component_type"], receiver=receiver, mlp_convention=d["mlp_convention"],
                   positions=positions, direction=d["direction"], freeze_patterns=d["freeze_patterns"])
