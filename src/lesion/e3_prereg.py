"""E3 pre-registration (D-016; the E3 spec,
``.superpowers/specs/2026-10-02-e3-functional-map-design.md``).

The block below is frozen by the pre-registration commit (before the first
GPU run), mirrored in results/E3/README.md, and both are pinned by
tests/test_e3_prereg.py. A change after results exist is a new
pre-registration: it goes to docs/04-decisions.md first and is listed in the
README below the block."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from src.lesion.spec import MLP, Component, Head


@dataclass(frozen=True)
class Item:
    name: str
    scheme: str  # the item's gated (default) corruption scheme
    prepend_bos: bool
    gate_file: str  # E1b gate artifact: the gap the scaled maps divide by, and the fraction removed
    floor_file: str  # E1b noise floor: validation gate 1 reproduces it


@dataclass(frozen=True)
class Map:
    id: str
    kind: Literal["total", "direct"]
    value: Literal["zero", "mean", "resample"]
    frozen: bool


def label(c: Component) -> str:
    return f"L{c.layer}H{c.head}" if isinstance(c, Head) else f"L{c.layer}.mlp"


def parse_label(s: str) -> Component:
    if m := re.fullmatch(r"L(\d+)H(\d+)", s):
        return Head(int(m.group(1)), int(m.group(2)))
    if m := re.fullmatch(r"L(\d+)\.mlp", s):
        return MLP(int(m.group(1)))
    raise ValueError(f"component must look like L9H6 or L0.mlp, got {s!r}")


# =================================== PRE-REGISTRATION ===================================
# D-016; the E3 spec. Frozen by the pre-registration commit, before the first GPU run.

N = 2000  # prompts per run
SEED = 0  # the selecting draw
HELD_OUT_SEED = 1  # the verification draw: a fresh draw, not disjoint prompts
REF_N = 2000  # every mean reference: corrupt side, template-matched (O-015)
REF_SEEDS = (0, 1, 2, 3, 4)  # selecting draw: the effect at the first, the spread over all five
HELD_OUT_REF_SEEDS = (5, 6, 7, 8, 9)  # held-out draw: the effect at the first, the spread over all five
BATCH_SIZE = 128  # the batch size of every E1b and E2 artifact the validation gates compare against
VALUES = ("zero", "mean", "resample")  # D-006
ALPHA = 0.05  # Holm-Bonferroni, family-wise, in every family
K = 10  # rule A: the top k by |effect| among a cell set's cells that clear Holm (ours)

ITEMS = (
    Item("ioi", "p_ABC", False, "results/E1b/gate/ioi/p_ABC.json", "results/E1b/noise/ioi/floor.json"),
    Item("induction", "fresh_prefix", True, "results/E1b/gate/induction/fresh_prefix.json",
         "results/E1b/noise/induction/floor.json"),
    Item("agreement", "number_flip", True, "results/E1b/gate/agreement/number_flip.json",
         "results/E1b/noise/agreement/floor.json"),
)

# 144 heads, then the 12 MLP layers (O-007): the 156 rows of every map; whole components,
# all positions (O-013).
COMPONENTS: tuple[Component, ...] = (tuple(Head(l, h) for l in range(12) for h in range(12))
                                     + tuple(MLP(l) for l in range(12)))

# Six total-effect maps (node, all positions, ablate-clean) and three direct-effect maps
# (edge to Logits, wang convention, unfrozen: the harness refuses freezing with edge ablation).
TOTAL_MAPS = tuple(Map(f"total_{v}_{'frozen' if f else 'unfrozen'}", "total", v, f)
                   for f in (False, True) for v in VALUES)
DIRECT_MAPS = tuple(Map(f"direct_{v}", "direct", v, False) for v in VALUES)

# The main Holm family: every total-effect cell, every direct-effect cell, every frozen delta.
N_TOTAL, N_DIRECT, N_DELTA = 2808, 1404, 1404
N_FAMILY = N_TOTAL + N_DIRECT + N_DELTA  # 5,616
FAMILIES = ("main", "verify_confirmatory", "verify_exploratory", "sufficiency_confirmatory",
            "sufficiency_exploratory", "adversarial")

# The second induction scheme, gated before use under D-014's thresholds, unchanged.
SHUFFLE_SCHEME = "shuffle_prefix"
GATE_ACC_MIN, GATE_GAP_MIN, GATE_TEMPLATE_FLOOR = 0.90, 1.0, 30

# Adversarial units: E2 I3's four heads singly and {5.5, 6.9} as a set, under all six
# total-effect maps; plus every induction selection under its selecting settings.
ADV_HEADS = (Head(5, 5), Head(6, 9), Head(4, 11), Head(2, 2))
ADV_SET = (Head(5, 5), Head(6, 9))
ADV_ARMS = ("shuffle_prefix", "end_only")  # each against the fresh_prefix, all-position baseline

# Validation gates (instrument checks, before any map is read).
GATE1_COMPONENTS: tuple[Component, ...] = tuple(MLP(l) for l in range(12)) + tuple(Head(l, 0) for l in range(12))
GATE2_DIR = "results/E2/I3"
DETERMINISM_CELLS = (("ioi", "total_mean_unfrozen", "L9H6"),
                     ("induction", "total_zero_frozen", "L5H5"),
                     ("agreement", "direct_resample", "L0.mlp"))

# ================================ END OF PRE-REGISTRATION ================================

ITEM = {i.name: i for i in ITEMS}
MAPS = TOTAL_MAPS + DIRECT_MAPS
MAP = {m.id: m for m in MAPS}
