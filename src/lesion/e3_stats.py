"""E3 statistics (D-016 items 3-5): the standard error per cell type, the z
test, Holm-Bonferroni, rule-A selection, and the fraction restored. Pure:
floats and lists in, dicts out; no model and no files.

    s (zero, resample cells)      the sem of per-prompt (clean - ablated) ld, from the runner
    s (mean cells)                max(sem, sd of effect_mean over reference seeds 0-4, or 5-9 held out)
    s (frozen delta, zero/resamp) the sem of per-prompt (frozen ablated - unfrozen ablated) ld
    s (frozen delta, mean)        max(that paired sem, sd of the delta over reference seeds)

z = |effect| / s, two-sided normal p. The normal approximation at n = 2,000
is stated, not tested. Non-finite inputs and s <= 0 are refused."""

from __future__ import annotations

import math
import statistics
from typing import Mapping, Sequence

from src.lesion.e2_reproduce import ranks


class StatsError(ValueError):
    """An input the statistics refuse rather than guess about."""


def _finite(**values: float) -> None:
    bad = [k for k, v in values.items() if not math.isfinite(v)]
    if bad:
        raise StatsError(f"non-finite {', '.join(bad)}")


def paired_sem(a: Sequence[float], b: Sequence[float]) -> float:
    """The sem of per-prompt differences a - b (float64, sample sd / sqrt(n))."""
    if len(a) != len(b):
        raise StatsError(f"paired columns differ in length: {len(a)} vs {len(b)}")
    if len(a) < 2:
        raise StatsError("a paired sem needs at least two prompts")
    d = [x - y for x, y in zip(a, b)]
    bad = [i for i, v in enumerate(d) if not math.isfinite(v)]
    if bad:
        raise StatsError(f"non-finite paired difference at prompts {bad[:5]}")
    return statistics.stdev(d) / math.sqrt(len(d))


def cell_s(sem: float, ref_effects: Sequence[float] | None) -> dict:
    """s for one cell. ``ref_effects`` is None for zero and resample; for a
    mean cell it is the effect (or delta) at every reference seed, the first
    being the cell's own."""
    _finite(sem=sem)
    if sem < 0:
        raise StatsError(f"negative sem {sem}")
    if ref_effects is None:
        return {"s": sem, "sem": sem, "ref_sd": None, "source": "sem"}
    if len(ref_effects) < 2:
        raise StatsError("a reference spread needs at least two reference seeds")
    for k, v in enumerate(ref_effects):
        _finite(**{f"ref_effects[{k}]": v})
    sd = statistics.stdev(ref_effects)
    return {"s": max(sem, sd), "sem": sem, "ref_sd": sd, "source": "ref_seed_sd" if sd >= sem else "sem"}


def z_test(effect: float, s: float) -> dict:
    _finite(effect=effect, s=s)
    if s <= 0:
        raise StatsError(f"s = {s}: a cell with no measured spread is refused, not tested")
    z = abs(effect) / s
    return {"z": z, "p": math.erfc(z / math.sqrt(2))}


def holm(p: Mapping[str, float], alpha: float) -> dict[str, dict]:
    """Holm-Bonferroni step-down at family-wise ``alpha``; valid under
    arbitrary dependence. Tests are sorted by (p, key), so tied p-values order
    deterministically; test i of m (1-based) is compared with
    alpha / (m - i + 1), and every test from the first failure on is not
    rejected."""
    for k, v in p.items():
        if not (math.isfinite(v) and 0.0 <= v <= 1.0):
            raise StatsError(f"p-value for {k!r} is {v}, not in [0, 1]")
    m = len(p)
    out: dict[str, dict] = {}
    failed = False
    for i, k in enumerate(sorted(p, key=lambda key: (p[key], key)), start=1):
        threshold = alpha / (m - i + 1)
        reject = not failed and p[k] <= threshold
        failed = failed or not reject
        out[k] = {"p": p[k], "step": i, "threshold": threshold, "reject": reject}
    return out


def select_rule_a(cells: Mapping[str, Mapping], k: int) -> dict:
    """D-016 item 4, within one cell set. ``cells``: component -> {"effect",
    "reject"}. Among the cells that clear Holm, competition ranks by |effect|
    (ties share the best rank); a component is selected iff its rank <= k, so
    a tie straddling rank k counts as inside. Sign is kept."""
    for c, v in cells.items():
        _finite(**{f"effect[{c}]": v["effect"]})
    cleared = {c: abs(v["effect"]) for c, v in cells.items() if v["reject"]}
    r = ranks(cleared, bottom=False) if cleared else {}
    chosen = sorted((c for c in cleared if r[c] <= k), key=lambda c: (r[c], c))
    return {"k": k, "n_cleared": len(cleared), "ranks": dict(sorted(r.items(), key=lambda kv: (kv[1], kv[0]))),
            "selected": [{"component": c, "effect": cells[c]["effect"], "rank": r[c]} for c in chosen],
            "tie_at_cut": len(chosen) > k}


def fraction_restored(effect: float, sem: float, gap: float) -> dict:
    """Restore-clean on the corrupt prompt: ``effect`` is mean(corrupt
    unintervened - corrupt restored) ld, so the share of the clean-minus-corrupt
    gap recovered is -effect / gap. Its sem is sem / |gap|; the gap's own
    spread is ignored, and the README says so."""
    _finite(effect=effect, sem=sem, gap=gap)
    if gap == 0:
        raise StatsError("gap = 0: no fraction to restore")
    return {"fraction_restored": -effect / gap, "fraction_sem": sem / abs(gap)}
