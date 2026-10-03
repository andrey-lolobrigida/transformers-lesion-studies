# E3 — Functional map

*Phase branch `phase-E3-functional-map`. Rules: D-016. Design: the E3 spec
(untracked, `.superpowers/specs/2026-10-02-e3-functional-map-design.md`).
Results sections are added after the runs; this file starts as the
pre-registration.*

## Pre-registration

This section mirrors the constant block at the top of
`src/lesion/e3_prereg.py`; `tests/test_e3_prereg.py` pins both. It was
committed before the first GPU run. A change to either after results exist is
a new pre-registration and is logged in `docs/04-decisions.md` first; code
changes after this commit are listed under "Changes after pre-registration"
below.

### Fixed settings

- GPT-2 small at HF revision `607a30d7`, TransformerLens 3.9.0, n = 2,000
  prompts per run, batch size 128 (the batch size of every E1b and E2
  artifact the validation gates compare against).
- Selecting draw: prompt seed 0. Held-out draw: prompt seed 1 (a fresh draw,
  not disjoint prompts; the overlap is counted per item).
- Mean references: corrupt side, template-matched, n = 2,000 (O-015), at
  reference seeds 0–4 on the selecting draw (effect at 0, spread over all
  five) and reference seeds 5–9 on the held-out draw (effect at 5).
- Items: IOI `p_ABC`, no BOS (D-011); induction `fresh_prefix`, BOS;
  agreement `number_flip`, BOS (ours, unsourced, D-013).
- Components: 144 heads and 12 MLP layers (156 rows), whole components at
  all positions (O-007, O-013).
- Metric: ld = logit[c] − logit[s] at END; effect = mean clean ld − mean
  ablated ld (positive: damage).

### Maps

Total effect, node, all positions, ablate-clean: `total_zero_unfrozen`,
`total_mean_unfrozen`, `total_resample_unfrozen`, `total_zero_frozen`,
`total_mean_frozen`, `total_resample_frozen`. Direct effect, edge to logits,
`wang` convention, unfrozen: `direct_zero`, `direct_mean`, `direct_resample`.
Frozen delta per (component, item, value): frozen effect − unfrozen effect.

### The confirmatory test

s per cell: the sem of per-prompt (clean − ablated) ld for zero and resample;
max(sem, sd of the effect over the reference seeds) for every mean cell; the
paired sem of per-prompt (frozen ablated − unfrozen ablated) ld for a zero or
resample delta, and max(that, sd of the delta over the reference seeds) for a
mean delta. z = |effect| / s, two-sided normal. Holm–Bonferroni at
family-wise α = 0.05 over one family, `main`: 2,808 total-effect cells +
1,404 direct-effect cells + 1,404 deltas = 5,616 tests. Non-finite inputs are
refused.

**Exact zeros.** A delta whose per-prompt differences are all exactly zero,
and for mean whose delta is zero at every reference seed, is exact by
construction: expected for the 13 layer-11 components (12 heads and the MLP),
which have no attention layer downstream for freezing to act on. It is
recorded as `exact_zero`, not tested, and keeps its place in the family with
p = 1, so m stays 5,616; this can only make Holm stricter. Any other s = 0
is a hard stop.

### Selection

Rule A, k = 10: within each cell set (one item × one map, 156 cells; 27 sets),
a component is selected iff its cell clears Holm and ranks in the top 10 by
|effect| among the set's cells that clear Holm. Sign kept. A tie straddling
rank 10 counts as inside. Deltas do not select. The confirmatory list is
written by `e3_select` and committed before any verification run. The
author's exploratory list (`{item, map, component, why}` per entry) is
committed before its own verification and labelled exploratory everywhere.

### Verification

Held-out replication gates naming: each selection re-run under its selecting
cell set's settings on prompt seed 1; replicated iff same sign and clears Holm
over its family (`verify_confirmatory`, `verify_exploratory`). Restore-clean
never gates: resample from the clean prompt onto the corrupt prompt, node,
all positions, unfrozen, prompt seed 1, once per (item, component) and once
per item for the set of that list's replicated heads (MLPs are left out of the
set: the set machinery is heads only); fraction of the gap restored, own Holm
families (`sufficiency_confirmatory`, `sufficiency_exploratory`).

### Adversarial checks (induction, measured, never gating)

`shuffle_prefix` (ours, unsourced: the first repeat permuted so no x_k is
followed by x_{k+1}) is gated before use under D-014's thresholds, unchanged:
pairwise accuracy ≥ 0.90, gap ≥ 1.0 logit, reference floor ≥ 30 per template
reported; n = 2,000, prompt seed 0, BOS. A failure is a null at full strength
and drops the scheme. Units: 5.5, 6.9, 4.11, 2.2 singly and {5.5, 6.9} as a
set under all six total-effect maps, plus every induction selection under its
own settings. Arms: `shuffle_prefix` (all positions) and END-only on
`fresh_prefix`, each against the `fresh_prefix` all-position baseline, on the
selecting draw; mean arms at reference seeds 0–4. One Holm family,
`adversarial`. Stated before running: the previous-token heads 4.11 and 2.2
act at B1, not END (E2 I4), so a small END-only effect for them is expected
and is not a refutation.

### Validation gates (before any map is read)

1. E1b identity: the 24 E1b noise components, unfrozen node mean at reference
   seeds 0–4, through the sweep driver, reproduce
   `results/E1b/noise/{item}/floor.json` bitwise.
2. E2 identity: E2 I3's single-unit cells reproduce the per-prompt columns of
   `results/E2/I3/` bitwise.
3. Determinism: (ioi, `total_mean_unfrozen`, L9H6), (induction,
   `total_zero_frozen`, L5H5), (agreement, `direct_resample`, L0.mlp), each
   run twice, bitwise identical.

## Changes after pre-registration

- `9154af6`, e3_maps.py (figures only): the Holm dot no longer overlaps a printed (clipped) MLP value, that value's font is larger, and the colorbar states the sign. No pre-registered value, test, or selection changes.
