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

*Everything below this line was written on 2026-10-09, after the runs, from
the committed artifacts. The Pre-registration section above is unchanged
since `96591d2`.*

**Conventions for every number below.** Components are written as the
artifacts write them (`L9H9` is head 9 of layer 9, 9.9 in E2's notation;
`L0.mlp` is layer 0's MLP). **Effect** is the mean over prompts of (clean
`ld` − ablated `ld`), so a positive effect means the ablation lowers the mean
logit difference and a negative one means it raises it. **s** is the
pre-registered standard error of a cell (sem of per-prompt differences for
zero and resample; max(sem, sd over the five reference seeds) for mean).
**Clears Holm** means the test is rejected at family-wise α = 0.05 inside the
named family (`main`, `verify_*`, `sufficiency_*`, `adversarial`).
**Fraction restored** is (mean `ld` with the clean activation written in −
mean corrupt `ld`) / (clean − corrupt gap), measured on the held-out draw.
**Fraction removed** is the share of the clean `ld` the item's corruption
scheme removes (D-014 item 2); it is cited beside every mean and resample
number. Mean references are on the corrupt side, template-matched, n = 2,000.

## 1. Commands and provenance

Paths are relative to `results/E3/`. Each command is the one recorded in the
artifacts' `command` field, which matches the plan's command for every
directory; where an artifact records no command, the table says so.

| Artifacts | Command | Recorded |
|---|---|---|
| `gates/{e1b_identity,e2_identity,determinism}.json` | `uv run python -m src.lesion.e3_gates --gate all` | `command` |
| `gates/induction/shuffle_prefix.{json,parquet}` | `uv run python -m src.lesion.e3_verify --stage gate-shuffle` | `command` |
| `sweep/{item}/` (27 cell sets, 3 clean files) | `uv run python -m src.lesion.e3_sweep --item all --stage selection` | `command` |
| `floor/{item}/` (36 cell sets) | `uv run python -m src.lesion.e3_sweep --item all --stage floor` | `command` |
| `selection/tests.json`, `selection/confirmatory.json` | `uv run python -m src.lesion.e3_select --stage confirmatory` | `command` |
| `selection/exploratory.json` | written by the author (no command) | — |
| `figures/` (18 PNGs) | `uv run python -m src.lesion.e3_maps` | not recorded (PNG files carry no record); the command is the module docstring's |
| `verify/{confirmatory,exploratory}/replication.json`, `heldout/` | `uv run python -m src.lesion.e3_verify --stage replicate --list {confirmatory,exploratory}` | `command` |
| `verify/{confirmatory,exploratory}/restore.json`, `restore/` | `uv run python -m src.lesion.e3_verify --stage restore --list {confirmatory,exploratory}` | `command` |
| `adversarial/adversarial.json`, `adversarial/arms.jsonl` | `uv run python -m src.lesion.e3_verify --stage adversarial` | `command` |
| `exit_confirmatory.json`, `exit_exploratory.json` | `uv run python -m src.lesion.e3_verify --stage table` | not recorded (the exit tables carry no `command`, `code_rev` or `environment`); the command is the module docstring's |
| Slow-tier checks on all of the above | `uv run pytest -q -m slow tests/test_e3_validation.py tests/test_e3_prereg.py` | — |

The sweep and the verification stages resume: rerunning the same command
skips finished cells (adversarial arms are reused from `arms.jsonl`).

**Provenance.**

- Pre-registration: commit `96591d2`, before the first GPU run.
- Confirmatory list (`selection/confirmatory.json` with `tests.json`):
  commit `109cc90`, before any verification run.
- Exploratory list (the author's): commit `7738b51`, before its verification.
- Verification, restore-clean, adversarial runs and exit tables: commit
  `133a8fe`. The by-construction ruling on adversarial arms: `785a33d`
  (D-016).
- Model: GPT-2 small at HF revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`
  (`607a30d7`); TransformerLens 3.9.0, torch 2.14.0+cu130, RTX 5060,
  deterministic algorithms on (each artifact's `environment`).
- Seeds: prompt seed 0 (selecting draw), 1 (held-out draw); mean reference
  seeds 0–4 (selecting) and 5–9 (held out); the adversarial arms run on the
  selecting draw at reference seeds 0–4.
- Code revision stamped on the cells (`code_rev`, the last commit touching
  `src/lesion/`): `1382046` on every sweep and floor cell and on the gate
  records; `9154af6` on every held-out cell and on the replication, restore
  and adversarial summary records (the per-run files under `restore/` carry
  `environment.repo_commit` only).
  `git diff 1382046..9154af6 -- src/lesion` touches `e3_maps.py` only (the
  figure fix listed under "Changes after pre-registration"), so the code that
  computed every number is the same. Each record's `environment.repo_commit`
  is the branch head when it was written: `96591d2` (gates), `7bd064c`
  (sweep and floor), `7738b51` (verification and adversarial).
- `git diff 96591d2..133a8fe -- src/` touches `e3_maps.py` only. The tests
  added after the pre-registration commit are the slow-tier exit checks in
  `tests/test_e3_validation.py` (Tasks 10–14) and the figure-layout test in
  `tests/test_e3_maps.py` (`9154af6`).

**Disk** (`du -sh results/E3/*`): `sweep/` 91M, `verify/` 16M, `floor/`
9.7M, `selection/` 3.0M, `figures/` 2.2M, `adversarial/` 556K,
`exit_confirmatory.json` 208K, `exit_exploratory.json` 20K, `gates/` 80K;
123M in all, this README included.

**GPU-hours: about 19.6, on one RTX 5060**, wall-clock. Derivation (the logs
carry no per-line timestamps, so each figure comes from the artifacts'
`environment.seconds` or from a log's start and last-write times):

| Stage | Source | Hours |
|---|---|---|
| Validation gates 1–3 | `environment.seconds` of the three gate records, summed (the log's last write, 22:07:15, is 36.6 min after the pre-registration commit at 21:30:39, an upper bound) | 0.56 |
| `shuffle_prefix` gate | `environment.seconds` (6.5 s) | 0.00 |
| Sweep, selection stage | 2026-10-02 22:08:36 (start) to 2026-10-03 04:17:53 (last write of `sweep-selection.log`) | 6.15 |
| Sweep, floor stage | 04:17:53 to 13:13:48 (last write of `sweep-floor.log`) | 8.93 |
| Replication, restore, adversarial | `environment.seconds` of the five records, summed | 3.98 |

The per-cell `seconds` fields of the 63 sweep and floor records sum to
15.58 h; that includes the gate-1 cells, which the sweep reused rather than
reran. The direct-effect smoke run (Task 10, n = 64, under `scratch/`) is not
counted.

PyTorch caching-allocator OOM-retry warnings appear in the gates, sweep,
verification and adversarial logs. Every run completed. Every
single-component adversarial baseline is compared bitwise with its seed-0
sweep cell before the arms are used (`check_baseline`, which raises
`VerifyError`), and none raised; the gates were bitwise too (§2).

## 2. Validation gates

All three gates passed on the first run (`uv run python -m src.lesion.e3_gates --gate all`):

1. E1b identity: the 24 E1b noise components, unfrozen node mean at
   reference seeds 0–4, through the sweep driver, reproduce
   `results/E1b/noise/{item}/floor.json` bitwise: 432 comparisons (144 per
   item), 0 mismatches.
2. E2 identity: E2 I3's single-unit cells reproduce the per-prompt columns of
   `results/E2/I3/` bitwise: 96 comparisons, 0 mismatches.
3. Determinism: the three named cells, each run twice, are bitwise identical
   in all six per-prompt columns: 3 comparisons.

**`shuffle_prefix` gate (D-014 thresholds, unchanged): PASS.** On
induction/`shuffle_prefix`, n = 2,000, seed 0, BOS: pairwise accuracy 0.999
(threshold 0.90), gap +17.288 ± 0.159 (threshold 1.0), fraction removed
1.017; reference floor at ref n 2,000, seed 0: per-template minimum 71 over 22
templates, none below 30. The accuracy and the clean mean `ld` (17.005) equal
the `fresh_prefix` gate's, as they must: the clean stream is shared. The
prediction written before the run, in the artifact's `prediction` field:
"corrupt mean ld near 0 by symmetry (both c and s stay in context)". Measured: −0.283 ± 0.087 (sem of the
corrupt `ld`), which is 3.3 sem below 0 and 0.016 of the gap in magnitude;
`fresh_prefix`'s corrupt mean `ld` is −0.007 ± 0.050. Both readings are
reported; no verdict on the prediction was pre-registered.

## 3. How to read the maps (stated before any number)

- **MLP rows.** Wang et al. [wang-2022 App. J] and Meng et al. [meng-2022
  App. B.2] found single-layer MLP effects small where multi-layer ones were
  large. The expected reading of these single-layer maps was therefore a
  blank MLP row, with MLP0 the expected exception on IOI (O-007 resolution,
  item 2). The measured rows are in §4.
- **IOI and induction overlap.** The IOI circuit contains the induction heads
  5.5 and 6.9 (`L5H5`, `L6H9`) (D-013). A component on both items' maps is
  not, by that fact, evidence of anything shared beyond this overlap; any
  cross-item reading starts from it.
- **Direct effect** is Wang et al.'s edge-to-logits effect, with the `wang`
  convention (`docs/01-methods.md`, as corrected in `b318591`; `ERRATA.md`):
  every other attention head's output is held at its clean value, while later
  MLPs and the final LayerNorm recompute, so their response to the component
  is inside the direct effect. It is not Pearl's mediation direct effect
  [meng-2022 §2.1 fn. 3], and it is not the component's own term. Total −
  direct is the net effect of the routes through later heads: it contains the
  component's own indirect effect as well as any compensation, and it misses
  compensation by later MLPs or the final LayerNorm. It is not a recorded
  field: it is computable per component from `selection/tests.json`
  (`total_{v}_unfrozen` − `direct_{v}`), is E4's baseline, and is not
  interpreted here beyond the aggregates in §8 (D-016 item 8).
- **Agreement is ours and unsourced** (D-013). Under mean ablation its
  reference mixes both subject numbers, half and half, because subject number
  is not in the template key (`results/E1b/README.md` §8); the fraction
  removed cited beside agreement mean numbers (2.002) describes the paired
  corrupt prompt, not that reference's direction.
- **Prior knowledge.** The published IOI and induction heads, and E2 I3's
  frozen-minus-unfrozen deltas, were seen before these rules were written.
  The selection rule is mechanical and was committed before the maps existed,
  but the choice of rule, of k and of the adversarial units was made by people
  who knew which heads the literature names.

## 4. The maps, per item

Each figure draws its maps together, never one alone: a 12 × 12 head grid
(layer down, head across) with the 12 MLP layers as a column at its right.
Red: the ablation lowers the mean `ld` (positive effect); blue: it raises it.
One symmetric scale per figure, set by the largest |head cell|; an MLP cell
beyond it is drawn at the end colour and printed with its value. A dot marks
a cell that clears Holm in `main`; an x marks an exact-zero delta. The
`_scaled` figures divide every cell by the item's clean − corrupt gap from
its E1b gate (seed 0).

**Delta figures.** Delta = frozen effect − unfrozen effect, per component and
value. A positive delta (red) means the ablation with patterns frozen lowers
the mean `ld` more than the same ablation with patterns recomputing (or raises
it less); a negative delta (blue) means it lowers it less (or raises it more).
The colorbar's "red: ld lowered" on these figures is loose shorthand for that.

"Cleared" counts the set's cells that clear Holm in `main`; "selected" is rule
A's top 10 among them. Deltas do not select. Every delta of the 13 layer-11
components is an exact zero (117 = 13 × 9, as predicted) and is not tested.

### IOI

Setting for every IOI number: ioi/`p_ABC`, no BOS (D-011), n = 2,000,
ablate-clean, all positions. Selecting draw: prompt seed 0, clean mean `ld`
3.651, gap 3.590 ± 0.053, fraction removed 0.983 (E1b gate). Mean reference
n 2,000, per-template minimum 52 at reference seed 0 (48 over seeds 0–4) and
50 at seed 5 on the held-out draw (43 over seeds 5–9). Held-out draw (prompt
seed 1): 3 of its 2,000 prompts also occur in the selecting draw.

- Total effect, six maps: [raw](figures/ioi_total_raw.png),
  [scaled](figures/ioi_total_scaled.png). Mean panels: ref n 2,000,
  reference seed 0, fraction removed 0.983. Resample panels: fraction removed
  0.983.
- Direct effect, three maps: [raw](figures/ioi_direct_raw.png),
  [scaled](figures/ioi_direct_scaled.png). Same reference and fraction removed.
- Frozen deltas, three maps: [raw](figures/ioi_delta_raw.png),
  [scaled](figures/ioi_delta_scaled.png). Same reference and fraction removed.

| Cell set | Cleared Holm | Selected | Tie at cut |
|---|---|---|---|
| `total_zero_unfrozen` | 140 | 10 | no |
| `total_mean_unfrozen` | 123 | 10 | no |
| `total_resample_unfrozen` | 110 | 10 | no |
| `total_zero_frozen` | 134 | 10 | no |
| `total_mean_frozen` | 95 | 10 | no |
| `total_resample_frozen` | 86 | 10 | no |
| `direct_zero` | 124 | 10 | no |
| `direct_mean` | 101 | 10 | no |
| `direct_resample` | 96 | 10 | no |
| `delta_zero` | 126 | — (deltas do not select) | — | 
| `delta_mean` | 114 | — (deltas do not select) | — | 
| `delta_resample` | 110 | — (deltas do not select) | — | 

MLP row: of IOI's 90 selections, 11 are MLP cells. `L0.mlp` is selected in 7
of the 9 sets; the other selected MLP cells are `L4.mlp` and `L5.mlp` (one set
each) and `L10.mlp` (two sets).

### Induction

Setting for every induction number: induction/`fresh_prefix`, BOS, n = 2,000,
ablate-clean, all positions unless a column says END-only. Selecting draw:
prompt seed 0, clean mean `ld` 17.005, gap 17.012 ± 0.138, fraction removed
1.000 (E1b gate). Mean reference n 2,000, per-template minimum 71 at
reference seed 0 (67 over seeds 0–4) and 69 at seed 5 on the held-out draw
(68 over seeds 5–9). Held-out draw: 0 of its 2,000 prompts occur in the
selecting draw.

- Total effect, six maps: [raw](figures/induction_total_raw.png),
  [scaled](figures/induction_total_scaled.png). Mean panels: ref n 2,000,
  reference seed 0, fraction removed 1.000. Resample panels: fraction removed
  1.000.
- Direct effect, three maps: [raw](figures/induction_direct_raw.png),
  [scaled](figures/induction_direct_scaled.png). Same reference and fraction
  removed.
- Frozen deltas, three maps: [raw](figures/induction_delta_raw.png),
  [scaled](figures/induction_delta_scaled.png). Same reference and fraction
  removed.

| Cell set | Cleared Holm | Selected | Tie at cut |
|---|---|---|---|
| `total_zero_unfrozen` | 133 | 10 | no |
| `total_mean_unfrozen` | 130 | 10 | no |
| `total_resample_unfrozen` | 131 | 10 | no |
| `total_zero_frozen` | 143 | 10 | no |
| `total_mean_frozen` | 140 | 10 | no |
| `total_resample_frozen` | 134 | 10 | no |
| `direct_zero` | 134 | 10 | no |
| `direct_mean` | 135 | 10 | no |
| `direct_resample` | 134 | 10 | no |
| `delta_zero` | 125 | — (deltas do not select) | — | 
| `delta_mean` | 109 | — (deltas do not select) | — | 
| `delta_resample` | 108 | — (deltas do not select) | — | 

MLP row: of induction's 90 selections, 42 are MLP cells, 35 of them in layers
other than 0; eight MLP layers are selected at least once (`L0`, `L4`, `L6`,
`L7`, `L8`, `L9`, `L10`, `L11`). The row is not blank.

### Agreement (ours, unsourced)

Setting for every agreement number: agreement/`number_flip`, BOS, n = 2,000,
ablate-clean, all positions. Selecting draw: prompt seed 0, clean mean `ld`
2.568, gap 5.141 ± 0.040, fraction removed 2.002 (E1b gate). Mean reference
n 2,000, per-template minimum 250 at every reference seed of both draws (8
templates; each mixes both subject numbers, §3). Held-out draw: 114 of its
2,000 prompts also occur in the selecting draw.

- Total effect, six maps: [raw](figures/agreement_total_raw.png),
  [scaled](figures/agreement_total_scaled.png). Mean panels: ref n 2,000,
  reference seed 0, fraction removed 2.002. Resample panels: fraction removed
  2.002.
- Direct effect, three maps: [raw](figures/agreement_direct_raw.png),
  [scaled](figures/agreement_direct_scaled.png). Same reference and fraction
  removed.
- Frozen deltas, three maps: [raw](figures/agreement_delta_raw.png),
  [scaled](figures/agreement_delta_scaled.png). Same reference and fraction
  removed.

| Cell set | Cleared Holm | Selected | Tie at cut |
|---|---|---|---|
| `total_zero_unfrozen` | 140 | 10 | no |
| `total_mean_unfrozen` | 98 | 10 | no |
| `total_resample_unfrozen` | 117 | 10 | no |
| `total_zero_frozen` | 137 | 10 | no |
| `total_mean_frozen` | 111 | 10 | no |
| `total_resample_frozen` | 125 | 10 | no |
| `direct_zero` | 134 | 10 | no |
| `direct_mean` | 104 | 10 | no |
| `direct_resample` | 120 | 10 | no |
| `delta_zero` | 125 | — (deltas do not select) | — | 
| `delta_mean` | 84 | — (deltas do not select) | — | 
| `delta_resample` | 92 | — (deltas do not select) | — | 

MLP row: of agreement's 90 selections, 43 are MLP cells, 36 of them in layers
other than 0; seven MLP layers are selected at least once (`L0`, `L5`, `L6`,
`L8`, `L9`, `L10`, `L11`). The row is not blank.

## 5. Exit tables

Every row below is one selection: the component, its cell set, the seed-0
effect ± s and its rank among the set's cells that clear Holm, the held-out
effect ± s (prompt seed 1; mean at reference seed 5, s over 5–9) and the
verdict (`replicated`: same sign and clears Holm in `verify_*`). The restore
column is per (item, component), so it repeats across a component's rows: the
fraction of the held-out gap restored by writing the component's clean output
into the corrupt run (resample from the clean prompt, node, all positions,
unfrozen), ± its sem, and whether it clears Holm in `sufficiency_*`. Restore
is a sufficiency reading and never gates. Mean rows carry ref n 2,000; mean
and resample rows carry the item's fraction removed (§4).

**The held-out draw's own numbers.** The held-out effects and every restore
fraction are measured on prompt seed 1. On that draw (`verify/*/restore.json`
`gaps`) the fraction removed is 1.001 (IOI), 0.996 (induction) and 2.007
(agreement), and the restore denominators are the gaps 3.645 ± 0.051 (IOI),
16.816 ± 0.133 (induction) and 5.163 ± 0.040 (agreement). The held-out cell
records themselves carry the selecting draw's E1b-gate value in
`context.fraction_removed` (0.983, 1.000, 2.002): the harness stamps the
item's gate value on every draw, so the numbers in this paragraph are the
held-out draw's own D-014 item 2 quantity.

**Induction adversarial columns** (on the selecting draw, against the
`fresh_prefix` all-position baseline, which is the row's seed-0 effect): the
`shuffle_prefix` arm (the same ablation on the `shuffle_prefix` corruption;
its mean arm uses the `shuffle_prefix` battery's own corrupt-side reference,
ref n 2,000, per-template minimum 71, and its fraction removed is 1.017) and
the END-only arm (the same ablation on `fresh_prefix`, at END only). Each
cell gives the arm's effect ± s, its sign against the baseline (`same` or
`flipped`), and whether it clears Holm in `adversarial`. Bold marks a flip or
a failure to clear. **"= baseline, by construction"** marks an arm that equals
its baseline cell exactly for a reason fixed by the design (D-016, ruling of
2026-10-09): `shuffle_prefix` under zero ablation (zero ablation never reads
the corrupt prompt, and the clean stream and answer tokens are shared with
`fresh_prefix`), END-only on a direct-effect map (the direct effect is read
at END only), END-only on `L11.mlp` (a last-layer MLP reaches the logits only
at its own position). Such an arm is uninformative and is left out of every
count of arms that held up; it stays in the Holm family as run.

### Confirmatory

270 selections (10 in each of the 27 cell sets), **270 replicated**, 0 not
replicated. Held-out / seed-0 effect ratio: 0.899 to 1.135 across the 270.
Restore: 50 of the 66 (item, component) singles clear Holm in
`sufficiency_confirmatory`; 16 do not (§6).

#### IOI (confirmatory)

| Component | Cell set | Seed 0 effect ± s | Rank | Held-out effect ± s | Verdict | Restored ± sem (Holm) |
|---|---|---|---|---|---|---|
| L0.mlp | `total_zero_unfrozen` | +5.056 ± 0.061 | 1 | +5.065 ± 0.060 | replicated | 0.813 ± 0.013 (clears) |
| L10H7 | `total_zero_unfrozen` | −1.388 ± 0.020 | 2 | −1.365 ± 0.020 | replicated | −0.4309 ± 0.0061 (clears) |
| L8H6 | `total_zero_unfrozen` | +1.173 ± 0.020 | 3 | +1.163 ± 0.020 | replicated | −0.0046 ± 0.0018 (does not clear) |
| L8H10 | `total_zero_unfrozen` | +1.026 ± 0.013 | 4 | +0.998 ± 0.014 | replicated | 0.0713 ± 0.0016 (clears) |
| L1H3 | `total_zero_unfrozen` | +0.933 ± 0.012 | 5 | +0.934 ± 0.011 | replicated | 0.00033 ± 0.00014 (does not clear) |
| L7H9 | `total_zero_unfrozen` | +0.8532 ± 0.0099 | 6 | +0.8550 ± 0.0097 | replicated | 0.0563 ± 0.0012 (clears) |
| L11H10 | `total_zero_unfrozen` | −0.830 ± 0.014 | 7 | −0.850 ± 0.013 | replicated | −0.2330 ± 0.0039 (clears) |
| L4.mlp | `total_zero_unfrozen` | +0.730 ± 0.021 | 8 | +0.703 ± 0.021 | replicated | −0.0293 ± 0.0014 (clears) |
| L10.mlp | `total_zero_unfrozen` | +0.711 ± 0.016 | 9 | +0.771 ± 0.016 | replicated | 0.0681 ± 0.0022 (clears) |
| L5H9 | `total_zero_unfrozen` | +0.675 ± 0.019 | 10 | +0.697 ± 0.019 | replicated | 0.00079 ± 0.00059 (does not clear) |
| L0.mlp | `total_mean_unfrozen` | +3.993 ± 0.040 | 1 | +3.909 ± 0.049 | replicated | 0.813 ± 0.013 (clears) |
| L10H7 | `total_mean_unfrozen` | −1.242 ± 0.019 | 2 | −1.217 ± 0.019 | replicated | −0.4309 ± 0.0061 (clears) |
| L8H6 | `total_mean_unfrozen` | +1.234 ± 0.022 | 3 | +1.218 ± 0.022 | replicated | −0.0046 ± 0.0018 (does not clear) |
| L5H5 | `total_mean_unfrozen` | +1.070 ± 0.012 | 4 | +1.068 ± 0.012 | replicated | 0.0011 ± 0.0016 (does not clear) |
| L8H10 | `total_mean_unfrozen` | +0.984 ± 0.011 | 5 | +0.965 ± 0.012 | replicated | 0.0713 ± 0.0016 (clears) |
| L7H9 | `total_mean_unfrozen` | +0.978 ± 0.012 | 6 | +0.984 ± 0.011 | replicated | 0.0563 ± 0.0012 (clears) |
| L11H10 | `total_mean_unfrozen` | −0.818 ± 0.013 | 7 | −0.840 ± 0.013 | replicated | −0.2330 ± 0.0039 (clears) |
| L3H0 | `total_mean_unfrozen` | +0.5352 ± 0.0064 | 8 | +0.5487 ± 0.0064 | replicated | −0.00251 ± 0.00089 (does not clear) |
| L7H3 | `total_mean_unfrozen` | +0.5150 ± 0.0080 | 9 | +0.5031 ± 0.0075 | replicated | 0.0342 ± 0.0013 (clears) |
| L9H6 | `total_mean_unfrozen` | −0.4574 ± 0.0086 | 10 | −0.4604 ± 0.0088 | replicated | 0.2875 ± 0.0057 (clears) |
| L0.mlp | `total_resample_unfrozen` | +4.468 ± 0.047 | 1 | +4.475 ± 0.045 | replicated | 0.813 ± 0.013 (clears) |
| L8H6 | `total_resample_unfrozen` | +1.237 ± 0.022 | 2 | +1.218 ± 0.022 | replicated | −0.0046 ± 0.0018 (does not clear) |
| L10H7 | `total_resample_unfrozen` | −1.231 ± 0.020 | 3 | −1.203 ± 0.020 | replicated | −0.4309 ± 0.0061 (clears) |
| L5H5 | `total_resample_unfrozen` | +1.076 ± 0.012 | 4 | +1.074 ± 0.012 | replicated | 0.0011 ± 0.0016 (does not clear) |
| L7H9 | `total_resample_unfrozen` | +0.997 ± 0.012 | 5 | +0.994 ± 0.012 | replicated | 0.0563 ± 0.0012 (clears) |
| L8H10 | `total_resample_unfrozen` | +0.983 ± 0.013 | 6 | +0.954 ± 0.013 | replicated | 0.0713 ± 0.0016 (clears) |
| L11H10 | `total_resample_unfrozen` | −0.819 ± 0.014 | 7 | −0.828 ± 0.014 | replicated | −0.2330 ± 0.0039 (clears) |
| L3H0 | `total_resample_unfrozen` | +0.5449 ± 0.0066 | 8 | +0.5586 ± 0.0065 | replicated | −0.00251 ± 0.00089 (does not clear) |
| L5.mlp | `total_resample_unfrozen` | +0.531 ± 0.015 | 9 | +0.536 ± 0.015 | replicated | −0.0178 ± 0.0018 (clears) |
| L7H3 | `total_resample_unfrozen` | +0.5230 ± 0.0098 | 10 | +0.5041 ± 0.0094 | replicated | 0.0342 ± 0.0013 (clears) |
| L9H9 | `total_zero_frozen` | +2.582 ± 0.027 | 1 | +2.587 ± 0.027 | replicated | 0.6907 ± 0.0071 (clears) |
| L10H7 | `total_zero_frozen` | −1.523 ± 0.021 | 2 | −1.504 ± 0.021 | replicated | −0.4309 ± 0.0061 (clears) |
| L9H6 | `total_zero_frozen` | +0.974 ± 0.019 | 3 | +0.965 ± 0.019 | replicated | 0.2875 ± 0.0057 (clears) |
| L11H10 | `total_zero_frozen` | −0.830 ± 0.014 | 4 | −0.850 ± 0.013 | replicated | −0.2330 ± 0.0039 (clears) |
| L0.mlp | `total_zero_frozen` | +0.761 ± 0.040 | 5 | +0.684 ± 0.040 | replicated | 0.813 ± 0.013 (clears) |
| L10H0 | `total_zero_frozen` | +0.724 ± 0.020 | 6 | +0.734 ± 0.020 | replicated | 0.2358 ± 0.0063 (clears) |
| L0H8 | `total_zero_frozen` | +0.706 ± 0.025 | 7 | +0.737 ± 0.024 | replicated | −0.00240 ± 0.00044 (clears) |
| L11H0 | `total_zero_frozen` | +0.605 ± 0.010 | 8 | +0.604 ± 0.010 | replicated | 0.00333 ± 0.00035 (clears) |
| L10H10 | `total_zero_frozen` | +0.4712 ± 0.0099 | 9 | +0.4699 ± 0.0099 | replicated | 0.1351 ± 0.0031 (clears) |
| L10.mlp | `total_zero_frozen` | +0.463 ± 0.012 | 10 | +0.472 ± 0.012 | replicated | 0.0681 ± 0.0022 (clears) |
| L9H9 | `total_mean_frozen` | +2.580 ± 0.026 | 1 | +2.577 ± 0.026 | replicated | 0.6907 ± 0.0071 (clears) |
| L0.mlp | `total_mean_frozen` | +2.177 ± 0.029 | 2 | +2.194 ± 0.027 | replicated | 0.813 ± 0.013 (clears) |
| L10H7 | `total_mean_frozen` | −1.552 ± 0.021 | 3 | −1.528 ± 0.021 | replicated | −0.4309 ± 0.0061 (clears) |
| L9H6 | `total_mean_frozen` | +0.977 ± 0.018 | 4 | +0.969 ± 0.018 | replicated | 0.2875 ± 0.0057 (clears) |
| L11H10 | `total_mean_frozen` | −0.818 ± 0.013 | 5 | −0.840 ± 0.013 | replicated | −0.2330 ± 0.0039 (clears) |
| L10H0 | `total_mean_frozen` | +0.754 ± 0.019 | 6 | +0.761 ± 0.019 | replicated | 0.2358 ± 0.0063 (clears) |
| L10H10 | `total_mean_frozen` | +0.4652 ± 0.0098 | 7 | +0.4646 ± 0.0099 | replicated | 0.1351 ± 0.0031 (clears) |
| L11H2 | `total_mean_frozen` | −0.373 ± 0.010 | 8 | −0.363 ± 0.011 | replicated | −0.0968 ± 0.0036 (clears) |
| L10H6 | `total_mean_frozen` | +0.270 ± 0.014 | 9 | +0.295 ± 0.013 | replicated | 0.0920 ± 0.0040 (clears) |
| L7H9 | `total_mean_frozen` | +0.2693 ± 0.0032 | 10 | +0.2731 ± 0.0032 | replicated | 0.0563 ± 0.0012 (clears) |
| L0.mlp | `total_resample_frozen` | +2.640 ± 0.043 | 1 | +2.666 ± 0.042 | replicated | 0.813 ± 0.013 (clears) |
| L9H9 | `total_resample_frozen` | +2.596 ± 0.027 | 2 | +2.595 ± 0.027 | replicated | 0.6907 ± 0.0071 (clears) |
| L10H7 | `total_resample_frozen` | −1.528 ± 0.022 | 3 | −1.500 ± 0.022 | replicated | −0.4309 ± 0.0061 (clears) |
| L9H6 | `total_resample_frozen` | +0.988 ± 0.020 | 4 | +0.980 ± 0.019 | replicated | 0.2875 ± 0.0057 (clears) |
| L11H10 | `total_resample_frozen` | −0.819 ± 0.014 | 5 | −0.828 ± 0.014 | replicated | −0.2330 ± 0.0039 (clears) |
| L10H0 | `total_resample_frozen` | +0.771 ± 0.021 | 6 | +0.777 ± 0.021 | replicated | 0.2358 ± 0.0063 (clears) |
| L10H10 | `total_resample_frozen` | +0.476 ± 0.011 | 7 | +0.465 ± 0.011 | replicated | 0.1351 ± 0.0031 (clears) |
| L11H2 | `total_resample_frozen` | −0.375 ± 0.012 | 8 | −0.355 ± 0.012 | replicated | −0.0968 ± 0.0036 (clears) |
| L10H6 | `total_resample_frozen` | +0.284 ± 0.015 | 9 | +0.314 ± 0.014 | replicated | 0.0920 ± 0.0040 (clears) |
| L7H9 | `total_resample_frozen` | +0.2729 ± 0.0038 | 10 | +0.2737 ± 0.0039 | replicated | 0.0563 ± 0.0012 (clears) |
| L9H9 | `direct_zero` | +2.503 ± 0.026 | 1 | +2.507 ± 0.026 | replicated | 0.6907 ± 0.0071 (clears) |
| L10H7 | `direct_zero` | −1.419 ± 0.020 | 2 | −1.402 ± 0.020 | replicated | −0.4309 ± 0.0061 (clears) |
| L9H6 | `direct_zero` | +0.951 ± 0.017 | 3 | +0.945 ± 0.017 | replicated | 0.2875 ± 0.0057 (clears) |
| L11H10 | `direct_zero` | −0.830 ± 0.014 | 4 | −0.850 ± 0.013 | replicated | −0.2330 ± 0.0039 (clears) |
| L10H0 | `direct_zero` | +0.694 ± 0.016 | 5 | +0.699 ± 0.016 | replicated | 0.2358 ± 0.0063 (clears) |
| L11H0 | `direct_zero` | +0.605 ± 0.010 | 6 | +0.604 ± 0.010 | replicated | 0.00333 ± 0.00035 (clears) |
| L10H10 | `direct_zero` | +0.4650 ± 0.0092 | 7 | +0.4645 ± 0.0092 | replicated | 0.1351 ± 0.0031 (clears) |
| L0.mlp | `direct_zero` | −0.4162 ± 0.0077 | 8 | −0.4392 ± 0.0083 | replicated | 0.813 ± 0.013 (clears) |
| L11H2 | `direct_zero` | −0.411 ± 0.010 | 9 | −0.400 ± 0.010 | replicated | −0.0968 ± 0.0036 (clears) |
| L8H10 | `direct_zero` | +0.3684 ± 0.0051 | 10 | +0.3720 ± 0.0052 | replicated | 0.0713 ± 0.0016 (clears) |
| L9H9 | `direct_mean` | +2.505 ± 0.025 | 1 | +2.502 ± 0.025 | replicated | 0.6907 ± 0.0071 (clears) |
| L10H7 | `direct_mean` | −1.520 ± 0.020 | 2 | −1.497 ± 0.020 | replicated | −0.4309 ± 0.0061 (clears) |
| L9H6 | `direct_mean` | +0.944 ± 0.017 | 3 | +0.939 ± 0.017 | replicated | 0.2875 ± 0.0057 (clears) |
| L11H10 | `direct_mean` | −0.818 ± 0.013 | 4 | −0.840 ± 0.013 | replicated | −0.2330 ± 0.0039 (clears) |
| L10H0 | `direct_mean` | +0.722 ± 0.015 | 5 | +0.725 ± 0.015 | replicated | 0.2358 ± 0.0063 (clears) |
| L10H10 | `direct_mean` | +0.4528 ± 0.0090 | 6 | +0.4527 ± 0.0092 | replicated | 0.1351 ± 0.0031 (clears) |
| L11H2 | `direct_mean` | −0.373 ± 0.010 | 7 | −0.363 ± 0.011 | replicated | −0.0968 ± 0.0036 (clears) |
| L10H6 | `direct_mean` | +0.259 ± 0.012 | 8 | +0.278 ± 0.011 | replicated | 0.0920 ± 0.0040 (clears) |
| L7H9 | `direct_mean` | +0.2591 ± 0.0031 | 9 | +0.2631 ± 0.0030 | replicated | 0.0563 ± 0.0012 (clears) |
| L8H10 | `direct_mean` | +0.2455 ± 0.0036 | 10 | +0.2452 ± 0.0036 | replicated | 0.0713 ± 0.0016 (clears) |
| L9H9 | `direct_resample` | +2.522 ± 0.026 | 1 | +2.520 ± 0.026 | replicated | 0.6907 ± 0.0071 (clears) |
| L10H7 | `direct_resample` | −1.496 ± 0.021 | 2 | −1.470 ± 0.021 | replicated | −0.4309 ± 0.0061 (clears) |
| L9H6 | `direct_resample` | +0.956 ± 0.018 | 3 | +0.948 ± 0.018 | replicated | 0.2875 ± 0.0057 (clears) |
| L11H10 | `direct_resample` | −0.819 ± 0.014 | 4 | −0.828 ± 0.014 | replicated | −0.2330 ± 0.0039 (clears) |
| L10H0 | `direct_resample` | +0.736 ± 0.017 | 5 | +0.737 ± 0.017 | replicated | 0.2358 ± 0.0063 (clears) |
| L10H10 | `direct_resample` | +0.463 ± 0.010 | 6 | +0.4537 ± 0.0100 | replicated | 0.1351 ± 0.0031 (clears) |
| L11H2 | `direct_resample` | −0.375 ± 0.012 | 7 | −0.355 ± 0.012 | replicated | −0.0968 ± 0.0036 (clears) |
| L10H6 | `direct_resample` | +0.270 ± 0.012 | 8 | +0.294 ± 0.012 | replicated | 0.0920 ± 0.0040 (clears) |
| L7H9 | `direct_resample` | +0.2618 ± 0.0036 | 9 | +0.2628 ± 0.0037 | replicated | 0.0563 ± 0.0012 (clears) |
| L8H10 | `direct_resample` | +0.2479 ± 0.0045 | 10 | +0.2467 ± 0.0045 | replicated | 0.0713 ± 0.0016 (clears) |

Rule-1 sentences, one per replicated component (settings as in §4; every
selection listed also replicated, see the table):

**L0.mlp** (7 cell sets, all replicated). Necessity: ablating L0.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +5.056 ± 0.061; mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +3.993 ± 0.040; resample, node, unfrozen [fraction removed 0.983]: +4.468 ± 0.047; zero, node, frozen: +0.761 ± 0.040; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +2.177 ± 0.029; resample, node, frozen [fraction removed 0.983]: +2.640 ± 0.043; zero, edge to logits, unfrozen: −0.4162 ± 0.0077. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0.mlp's clean output into the corrupt run restores 0.813 ± 0.013 of the gap (clears Holm).

**L10H7** (9 cell sets, all replicated). Necessity: ablating L10H7 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: −1.388 ± 0.020; mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: −1.242 ± 0.019; resample, node, unfrozen [fraction removed 0.983]: −1.231 ± 0.020; zero, node, frozen: −1.523 ± 0.021; mean, node, frozen [ref n 2,000; fraction removed 0.983]: −1.552 ± 0.021; resample, node, frozen [fraction removed 0.983]: −1.528 ± 0.022; zero, edge to logits, unfrozen: −1.419 ± 0.020; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: −1.520 ± 0.020; resample, edge to logits, unfrozen [fraction removed 0.983]: −1.496 ± 0.021. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H7's clean output into the corrupt run restores −0.4309 ± 0.0061 of the gap (clears Holm).

**L8H6** (3 cell sets, all replicated). Necessity: ablating L8H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +1.173 ± 0.020; mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +1.234 ± 0.022; resample, node, unfrozen [fraction removed 0.983]: +1.237 ± 0.022. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8H6's clean output into the corrupt run restores −0.0046 ± 0.0018 of the gap (does not clear Holm).

**L8H10** (6 cell sets, all replicated). Necessity: ablating L8H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +1.026 ± 0.013; mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.984 ± 0.011; resample, node, unfrozen [fraction removed 0.983]: +0.983 ± 0.013; zero, edge to logits, unfrozen: +0.3684 ± 0.0051; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +0.2455 ± 0.0036; resample, edge to logits, unfrozen [fraction removed 0.983]: +0.2479 ± 0.0045. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8H10's clean output into the corrupt run restores 0.0713 ± 0.0016 of the gap (clears Holm).

**L1H3** (1 cell set, replicated). Necessity: ablating L1H3 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.933 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L1H3's clean output into the corrupt run restores 0.00033 ± 0.00014 of the gap (does not clear Holm).

**L7H9** (7 cell sets, all replicated). Necessity: ablating L7H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.8532 ± 0.0099; mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.978 ± 0.012; resample, node, unfrozen [fraction removed 0.983]: +0.997 ± 0.012; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +0.2693 ± 0.0032; resample, node, frozen [fraction removed 0.983]: +0.2729 ± 0.0038; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +0.2591 ± 0.0031; resample, edge to logits, unfrozen [fraction removed 0.983]: +0.2618 ± 0.0036. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L7H9's clean output into the corrupt run restores 0.0563 ± 0.0012 of the gap (clears Holm).

**L11H10** (9 cell sets, all replicated). Necessity: ablating L11H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: −0.830 ± 0.014; mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: −0.818 ± 0.013; resample, node, unfrozen [fraction removed 0.983]: −0.819 ± 0.014; zero, node, frozen: −0.830 ± 0.014; mean, node, frozen [ref n 2,000; fraction removed 0.983]: −0.818 ± 0.013; resample, node, frozen [fraction removed 0.983]: −0.819 ± 0.014; zero, edge to logits, unfrozen: −0.830 ± 0.014; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: −0.818 ± 0.013; resample, edge to logits, unfrozen [fraction removed 0.983]: −0.819 ± 0.014. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H10's clean output into the corrupt run restores −0.2330 ± 0.0039 of the gap (clears Holm).

**L4.mlp** (1 cell set, replicated). Necessity: ablating L4.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.730 ± 0.021. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L4.mlp's clean output into the corrupt run restores −0.0293 ± 0.0014 of the gap (clears Holm).

**L10.mlp** (2 cell sets, all replicated). Necessity: ablating L10.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.711 ± 0.016; zero, node, frozen: +0.463 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10.mlp's clean output into the corrupt run restores 0.0681 ± 0.0022 of the gap (clears Holm).

**L5H9** (1 cell set, replicated). Necessity: ablating L5H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.675 ± 0.019. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5H9's clean output into the corrupt run restores 0.00079 ± 0.00059 of the gap (does not clear Holm).

**L5H5** (2 cell sets, all replicated). Necessity: ablating L5H5 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +1.070 ± 0.012; resample, node, unfrozen [fraction removed 0.983]: +1.076 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5H5's clean output into the corrupt run restores 0.0011 ± 0.0016 of the gap (does not clear Holm).

**L3H0** (2 cell sets, all replicated). Necessity: ablating L3H0 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.5352 ± 0.0064; resample, node, unfrozen [fraction removed 0.983]: +0.5449 ± 0.0066. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L3H0's clean output into the corrupt run restores −0.00251 ± 0.00089 of the gap (does not clear Holm).

**L7H3** (2 cell sets, all replicated). Necessity: ablating L7H3 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.5150 ± 0.0080; resample, node, unfrozen [fraction removed 0.983]: +0.5230 ± 0.0098. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L7H3's clean output into the corrupt run restores 0.0342 ± 0.0013 of the gap (clears Holm).

**L9H6** (7 cell sets, all replicated). Necessity: ablating L9H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: −0.4574 ± 0.0086; zero, node, frozen: +0.974 ± 0.019; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +0.977 ± 0.018; resample, node, frozen [fraction removed 0.983]: +0.988 ± 0.020; zero, edge to logits, unfrozen: +0.951 ± 0.017; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +0.944 ± 0.017; resample, edge to logits, unfrozen [fraction removed 0.983]: +0.956 ± 0.018. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9H6's clean output into the corrupt run restores 0.2875 ± 0.0057 of the gap (clears Holm).

**L5.mlp** (1 cell set, replicated). Necessity: ablating L5.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, node, unfrozen [fraction removed 0.983]: +0.531 ± 0.015. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5.mlp's clean output into the corrupt run restores −0.0178 ± 0.0018 of the gap (clears Holm).

**L9H9** (6 cell sets, all replicated). Necessity: ablating L9H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +2.582 ± 0.027; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +2.580 ± 0.026; resample, node, frozen [fraction removed 0.983]: +2.596 ± 0.027; zero, edge to logits, unfrozen: +2.503 ± 0.026; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +2.505 ± 0.025; resample, edge to logits, unfrozen [fraction removed 0.983]: +2.522 ± 0.026. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9H9's clean output into the corrupt run restores 0.6907 ± 0.0071 of the gap (clears Holm).

**L10H0** (6 cell sets, all replicated). Necessity: ablating L10H0 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +0.724 ± 0.020; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +0.754 ± 0.019; resample, node, frozen [fraction removed 0.983]: +0.771 ± 0.021; zero, edge to logits, unfrozen: +0.694 ± 0.016; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +0.722 ± 0.015; resample, edge to logits, unfrozen [fraction removed 0.983]: +0.736 ± 0.017. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H0's clean output into the corrupt run restores 0.2358 ± 0.0063 of the gap (clears Holm).

**L0H8** (1 cell set, replicated). Necessity: ablating L0H8 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +0.706 ± 0.025. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0H8's clean output into the corrupt run restores −0.00240 ± 0.00044 of the gap (clears Holm).

**L11H0** (2 cell sets, all replicated). Necessity: ablating L11H0 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +0.605 ± 0.010; zero, edge to logits, unfrozen: +0.605 ± 0.010. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H0's clean output into the corrupt run restores 0.00333 ± 0.00035 of the gap (clears Holm).

**L10H10** (6 cell sets, all replicated). Necessity: ablating L10H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +0.4712 ± 0.0099; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +0.4652 ± 0.0098; resample, node, frozen [fraction removed 0.983]: +0.476 ± 0.011; zero, edge to logits, unfrozen: +0.4650 ± 0.0092; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +0.4528 ± 0.0090; resample, edge to logits, unfrozen [fraction removed 0.983]: +0.463 ± 0.010. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H10's clean output into the corrupt run restores 0.1351 ± 0.0031 of the gap (clears Holm).

**L11H2** (5 cell sets, all replicated). Necessity: ablating L11H2 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, frozen [ref n 2,000; fraction removed 0.983]: −0.373 ± 0.010; resample, node, frozen [fraction removed 0.983]: −0.375 ± 0.012; zero, edge to logits, unfrozen: −0.411 ± 0.010; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: −0.373 ± 0.010; resample, edge to logits, unfrozen [fraction removed 0.983]: −0.375 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H2's clean output into the corrupt run restores −0.0968 ± 0.0036 of the gap (clears Holm).

**L10H6** (4 cell sets, all replicated). Necessity: ablating L10H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, frozen [ref n 2,000; fraction removed 0.983]: +0.270 ± 0.014; resample, node, frozen [fraction removed 0.983]: +0.284 ± 0.015; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 0.983]: +0.259 ± 0.012; resample, edge to logits, unfrozen [fraction removed 0.983]: +0.270 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H6's clean output into the corrupt run restores 0.0920 ± 0.0040 of the gap (clears Holm).

#### Induction (confirmatory)

| Component | Cell set | Seed 0 effect ± s | Rank | Held-out effect ± s | Verdict | Restored ± sem (Holm) | `shuffle_prefix` arm | END-only arm |
|---|---|---|---|---|---|---|---|---|
| L0.mlp | `total_zero_unfrozen` | +15.525 ± 0.166 | 1 | +15.524 ± 0.164 | replicated | 0.9027 ± 0.0071 (clears) | = baseline, by construction | +4.422 ± 0.118, same, clears |
| L5H1 | `total_zero_unfrozen` | +4.361 ± 0.075 | 2 | +4.187 ± 0.072 | replicated | 0.0564 ± 0.0011 (clears) | = baseline, by construction | +1.266 ± 0.037, same, clears |
| L7H6 | `total_zero_unfrozen` | +3.202 ± 0.050 | 3 | +3.134 ± 0.048 | replicated | −0.01027 ± 0.00064 (clears) | = baseline, by construction | +2.774 ± 0.043, same, clears |
| L4H11 | `total_zero_unfrozen` | +3.166 ± 0.061 | 4 | +3.089 ± 0.058 | replicated | 0.00028 ± 0.00053 (does not clear) | = baseline, by construction | +0.0771 ± 0.0087, same, clears |
| L0H1 | `total_zero_unfrozen` | +3.096 ± 0.083 | 5 | +2.886 ± 0.076 | replicated | 0.0013 ± 0.0016 (does not clear) | = baseline, by construction | +0.402 ± 0.019, same, clears |
| L5H9 | `total_zero_unfrozen` | +2.845 ± 0.052 | 6 | +2.737 ± 0.049 | replicated | −0.00034 ± 0.00051 (does not clear) | = baseline, by construction | +0.410 ± 0.013, same, clears |
| L0H3 | `total_zero_unfrozen` | +2.251 ± 0.054 | 7 | +2.213 ± 0.053 | replicated | −0.00034 ± 0.00020 (does not clear) | = baseline, by construction | +0.237 ± 0.014, same, clears |
| L0H11 | `total_zero_unfrozen` | −2.028 ± 0.043 | 8 | −2.038 ± 0.040 | replicated | −0.00016 ± 0.00011 (does not clear) | = baseline, by construction | −0.267 ± 0.021, same, clears |
| L1H10 | `total_zero_unfrozen` | +2.012 ± 0.056 | 9 | +1.871 ± 0.052 | replicated | −0.000033 ± 0.000049 (does not clear) | = baseline, by construction | +1.095 ± 0.054, same, clears |
| L11.mlp | `total_zero_unfrozen` | −1.752 ± 0.045 | 10 | −1.723 ± 0.045 | replicated | 0.0960 ± 0.0025 (clears) | = baseline, by construction | = baseline, by construction |
| L0.mlp | `total_mean_unfrozen` | +13.725 ± 0.142 | 1 | +13.808 ± 0.140 | replicated | 0.9027 ± 0.0071 (clears) | +13.900 ± 0.156, same, clears | +3.174 ± 0.094, same, clears |
| L5H1 | `total_mean_unfrozen` | +6.303 ± 0.086 | 2 | +6.100 ± 0.083 | replicated | 0.0564 ± 0.0011 (clears) | +4.868 ± 0.074, same, clears | +2.979 ± 0.060, same, clears |
| L4H11 | `total_mean_unfrozen` | +3.209 ± 0.061 | 3 | +3.120 ± 0.057 | replicated | 0.00028 ± 0.00053 (does not clear) | +2.993 ± 0.060, same, clears | +0.1506 ± 0.0085, same, clears |
| L4.mlp | `total_mean_unfrozen` | +2.201 ± 0.064 | 4 | +2.131 ± 0.062 | replicated | 0.00064 ± 0.00057 (does not clear) | +1.734 ± 0.061, same, clears | +0.366 ± 0.024, same, clears |
| L9.mlp | `total_mean_unfrozen` | +2.094 ± 0.043 | 5 | +2.030 ± 0.041 | replicated | 0.0707 ± 0.0012 (clears) | +1.130 ± 0.035, same, clears | +1.948 ± 0.041, same, clears |
| L10.mlp | `total_mean_unfrozen` | +2.090 ± 0.041 | 6 | +2.035 ± 0.040 | replicated | 0.1248 ± 0.0016 (clears) | +1.522 ± 0.037, same, clears | +2.022 ± 0.040, same, clears |
| L8H5 | `total_mean_unfrozen` | +2.075 ± 0.041 | 7 | +2.046 ± 0.041 | replicated | 0.00225 ± 0.00031 (clears) | +1.294 ± 0.031, same, clears | +1.734 ± 0.035, same, clears |
| L7H6 | `total_mean_unfrozen` | +1.992 ± 0.043 | 8 | +1.910 ± 0.041 | replicated | −0.01027 ± 0.00064 (clears) | +1.290 ± 0.038, same, clears | +1.654 ± 0.037, same, clears |
| L7.mlp | `total_mean_unfrozen` | +1.991 ± 0.053 | 9 | +1.886 ± 0.050 | replicated | 0.0435 ± 0.0010 (clears) | +1.416 ± 0.046, same, clears | +1.511 ± 0.043, same, clears |
| L6H7 | `total_mean_unfrozen` | +1.831 ± 0.037 | 10 | +1.779 ± 0.037 | replicated | 0.00031 ± 0.00038 (does not clear) | +1.201 ± 0.027, same, clears | +0.896 ± 0.022, same, clears |
| L0.mlp | `total_resample_unfrozen` | +16.986 ± 0.138 | 1 | +16.797 ± 0.133 | replicated | 0.9027 ± 0.0071 (clears) | +17.128 ± 0.157, same, clears | +1.845 ± 0.048, same, clears |
| L5H1 | `total_resample_unfrozen` | +6.301 ± 0.086 | 2 | +6.101 ± 0.083 | replicated | 0.0564 ± 0.0011 (clears) | +4.872 ± 0.075, same, clears | +2.983 ± 0.061, same, clears |
| L4H11 | `total_resample_unfrozen` | +5.248 ± 0.082 | 3 | +5.031 ± 0.079 | replicated | 0.00028 ± 0.00053 (does not clear) | +4.938 ± 0.084, same, clears | +0.0966 ± 0.0059, same, clears |
| L0H1 | `total_resample_unfrozen` | +2.771 ± 0.065 | 4 | +2.723 ± 0.064 | replicated | 0.0013 ± 0.0016 (does not clear) | +0.280 ± 0.038, same, clears | +1.375 ± 0.039, same, clears |
| L9.mlp | `total_resample_unfrozen` | +2.276 ± 0.047 | 5 | +2.208 ± 0.045 | replicated | 0.0707 ± 0.0012 (clears) | +1.323 ± 0.041, same, clears | +2.101 ± 0.045, same, clears |
| L7.mlp | `total_resample_unfrozen` | +2.251 ± 0.057 | 6 | +2.146 ± 0.055 | replicated | 0.0435 ± 0.0010 (clears) | +1.668 ± 0.050, same, clears | +1.716 ± 0.047, same, clears |
| L10.mlp | `total_resample_unfrozen` | +2.192 ± 0.044 | 7 | +2.121 ± 0.043 | replicated | 0.1248 ± 0.0016 (clears) | +1.739 ± 0.043, same, clears | +2.117 ± 0.043, same, clears |
| L4.mlp | `total_resample_unfrozen` | +2.067 ± 0.066 | 8 | +1.973 ± 0.063 | replicated | 0.00064 ± 0.00057 (does not clear) | +1.567 ± 0.061, same, clears | +0.180 ± 0.013, same, clears |
| L8H5 | `total_resample_unfrozen` | +2.063 ± 0.042 | 9 | +2.035 ± 0.041 | replicated | 0.00225 ± 0.00031 (clears) | +1.297 ± 0.031, same, clears | +1.725 ± 0.036, same, clears |
| L7H6 | `total_resample_unfrozen` | +2.012 ± 0.043 | 10 | +1.924 ± 0.041 | replicated | −0.01027 ± 0.00064 (clears) | +1.296 ± 0.038, same, clears | +1.677 ± 0.038, same, clears |
| L0.mlp | `total_zero_frozen` | +3.370 ± 0.105 | 1 | +3.358 ± 0.106 | replicated | 0.9027 ± 0.0071 (clears) | = baseline, by construction | **−0.641 ± 0.027, flipped, clears** |
| L5H1 | `total_zero_frozen` | +2.932 ± 0.060 | 2 | +2.853 ± 0.059 | replicated | 0.0564 ± 0.0011 (clears) | = baseline, by construction | **−0.089 ± 0.021, flipped, clears** |
| L7H6 | `total_zero_frozen` | +2.528 ± 0.041 | 3 | +2.463 ± 0.039 | replicated | −0.01027 ± 0.00064 (clears) | = baseline, by construction | +2.153 ± 0.035, same, clears |
| L0H11 | `total_zero_frozen` | −2.186 ± 0.030 | 4 | −2.170 ± 0.030 | replicated | −0.00016 ± 0.00011 (does not clear) | = baseline, by construction | −0.503 ± 0.012, same, clears |
| L10.mlp | `total_zero_frozen` | +2.009 ± 0.034 | 5 | +1.992 ± 0.034 | replicated | 0.1248 ± 0.0016 (clears) | = baseline, by construction | +1.805 ± 0.034, same, clears |
| L11.mlp | `total_zero_frozen` | −1.752 ± 0.045 | 6 | −1.723 ± 0.045 | replicated | 0.0960 ± 0.0025 (clears) | = baseline, by construction | = baseline, by construction |
| L0H3 | `total_zero_frozen` | +1.723 ± 0.044 | 7 | +1.693 ± 0.040 | replicated | −0.00034 ± 0.00020 (does not clear) | = baseline, by construction | +0.2140 ± 0.0078, same, clears |
| L6.mlp | `total_zero_frozen` | +1.557 ± 0.034 | 8 | +1.480 ± 0.032 | replicated | −0.00310 ± 0.00079 (clears) | = baseline, by construction | +0.315 ± 0.017, same, clears |
| L5H9 | `total_zero_frozen` | +1.464 ± 0.031 | 9 | +1.439 ± 0.031 | replicated | −0.00034 ± 0.00051 (does not clear) | = baseline, by construction | +0.5868 ± 0.0085, same, clears |
| L7.mlp | `total_zero_frozen` | +1.385 ± 0.035 | 10 | +1.304 ± 0.033 | replicated | 0.0435 ± 0.0010 (clears) | = baseline, by construction | +0.853 ± 0.027, same, clears |
| L5H1 | `total_mean_frozen` | +4.550 ± 0.074 | 1 | +4.450 ± 0.072 | replicated | 0.0564 ± 0.0011 (clears) | +3.593 ± 0.063, same, clears | +1.191 ± 0.035, same, clears |
| L10.mlp | `total_mean_frozen` | +2.204 ± 0.038 | 2 | +2.182 ± 0.037 | replicated | 0.1248 ± 0.0016 (clears) | +1.611 ± 0.033, same, clears | +2.156 ± 0.036, same, clears |
| L9.mlp | `total_mean_frozen` | +1.916 ± 0.034 | 3 | +1.882 ± 0.033 | replicated | 0.0707 ± 0.0012 (clears) | +0.899 ± 0.027, same, clears | +1.774 ± 0.032, same, clears |
| L7H6 | `total_mean_frozen` | +1.742 ± 0.035 | 4 | +1.669 ± 0.032 | replicated | −0.01027 ± 0.00064 (clears) | +1.143 ± 0.030, same, clears | +1.400 ± 0.030, same, clears |
| L7.mlp | `total_mean_frozen` | +1.710 ± 0.039 | 5 | +1.625 ± 0.037 | replicated | 0.0435 ± 0.0010 (clears) | +1.213 ± 0.032, same, clears | +0.979 ± 0.030, same, clears |
| L0H1 | `total_mean_frozen` | +1.549 ± 0.036 | 6 | +1.553 ± 0.035 | replicated | 0.0013 ± 0.0016 (does not clear) | **−0.076 ± 0.015, flipped, clears** | +0.633 ± 0.018, same, clears |
| L8H5 | `total_mean_frozen` | +1.534 ± 0.031 | 7 | +1.524 ± 0.031 | replicated | 0.00225 ± 0.00031 (clears) | +0.878 ± 0.022, same, clears | +1.313 ± 0.027, same, clears |
| L0.mlp | `total_mean_frozen` | +1.276 ± 0.110 | 8 | +1.227 ± 0.110 | replicated | 0.9027 ± 0.0071 (clears) | +1.250 ± 0.107, same, clears | **−0.473 ± 0.025, flipped, clears** |
| L10H7 | `total_mean_frozen` | −1.274 ± 0.017 | 9 | −1.275 ± 0.018 | replicated | −0.0838 ± 0.0013 (clears) | −0.948 ± 0.018, same, clears | −1.267 ± 0.017, same, clears |
| L6.mlp | `total_mean_frozen` | +1.151 ± 0.030 | 10 | +1.088 ± 0.028 | replicated | −0.00310 ± 0.00079 (clears) | +1.331 ± 0.032, same, clears | +0.296 ± 0.017, same, clears |
| L0.mlp | `total_resample_frozen` | +13.698 ± 0.141 | 1 | +13.465 ± 0.140 | replicated | 0.9027 ± 0.0071 (clears) | +13.082 ± 0.170, same, clears | +1.202 ± 0.030, same, clears |
| L5H1 | `total_resample_frozen` | +4.550 ± 0.074 | 2 | +4.450 ± 0.072 | replicated | 0.0564 ± 0.0011 (clears) | +3.551 ± 0.064, same, clears | +1.191 ± 0.035, same, clears |
| L10.mlp | `total_resample_frozen` | +2.318 ± 0.040 | 3 | +2.275 ± 0.039 | replicated | 0.1248 ± 0.0016 (clears) | +1.781 ± 0.038, same, clears | +2.260 ± 0.039, same, clears |
| L0H1 | `total_resample_frozen` | +2.178 ± 0.049 | 4 | +2.169 ± 0.047 | replicated | 0.0013 ± 0.0016 (does not clear) | +0.266 ± 0.018, same, clears | +1.005 ± 0.026, same, clears |
| L9.mlp | `total_resample_frozen` | +2.104 ± 0.038 | 5 | +2.059 ± 0.037 | replicated | 0.0707 ± 0.0012 (clears) | +1.054 ± 0.032, same, clears | +1.959 ± 0.036, same, clears |
| L7.mlp | `total_resample_frozen` | +2.005 ± 0.043 | 6 | +1.916 ± 0.041 | replicated | 0.0435 ± 0.0010 (clears) | +1.482 ± 0.037, same, clears | +1.235 ± 0.033, same, clears |
| L7H6 | `total_resample_frozen` | +1.740 ± 0.035 | 7 | +1.668 ± 0.033 | replicated | −0.01027 ± 0.00064 (clears) | +1.132 ± 0.030, same, clears | +1.399 ± 0.030, same, clears |
| L8H5 | `total_resample_frozen` | +1.530 ± 0.032 | 8 | +1.520 ± 0.031 | replicated | 0.00225 ± 0.00031 (clears) | +0.886 ± 0.022, same, clears | +1.312 ± 0.027, same, clears |
| L6.mlp | `total_resample_frozen` | +1.474 ± 0.033 | 9 | +1.402 ± 0.032 | replicated | −0.00310 ± 0.00079 (clears) | +1.614 ± 0.035, same, clears | +0.488 ± 0.018, same, clears |
| L8.mlp | `total_resample_frozen` | +1.319 ± 0.031 | 10 | +1.247 ± 0.032 | replicated | 0.0489 ± 0.0010 (clears) | +1.012 ± 0.027, same, clears | +1.120 ± 0.029, same, clears |
| L7H6 | `direct_zero` | +2.047 ± 0.033 | 1 | +1.994 ± 0.030 | replicated | −0.01027 ± 0.00064 (clears) | = baseline, by construction | = baseline, by construction |
| L11.mlp | `direct_zero` | −1.752 ± 0.045 | 2 | −1.723 ± 0.045 | replicated | 0.0960 ± 0.0025 (clears) | = baseline, by construction | = baseline, by construction |
| L10.mlp | `direct_zero` | +1.749 ± 0.032 | 3 | +1.741 ± 0.032 | replicated | 0.1248 ± 0.0016 (clears) | = baseline, by construction | = baseline, by construction |
| L6H9 | `direct_zero` | −0.931 ± 0.024 | 4 | −0.909 ± 0.022 | replicated | 0.07682 ± 0.00094 (clears) | = baseline, by construction | = baseline, by construction |
| L10H7 | `direct_zero` | −0.900 ± 0.018 | 5 | −0.896 ± 0.018 | replicated | −0.0838 ± 0.0013 (clears) | = baseline, by construction | = baseline, by construction |
| L11H0 | `direct_zero` | +0.868 ± 0.041 | 6 | +0.906 ± 0.040 | replicated | −0.00006 ± 0.00020 (does not clear) | = baseline, by construction | = baseline, by construction |
| L9H6 | `direct_zero` | +0.806 ± 0.016 | 7 | +0.809 ± 0.017 | replicated | 0.0777 ± 0.0013 (clears) | = baseline, by construction | = baseline, by construction |
| L11H10 | `direct_zero` | −0.797 ± 0.016 | 8 | −0.798 ± 0.016 | replicated | −0.04813 ± 0.00092 (clears) | = baseline, by construction | = baseline, by construction |
| L8H5 | `direct_zero` | +0.782 ± 0.020 | 9 | +0.770 ± 0.020 | replicated | 0.00225 ± 0.00031 (clears) | = baseline, by construction | = baseline, by construction |
| L9.mlp | `direct_zero` | +0.757 ± 0.025 | 10 | +0.747 ± 0.026 | replicated | 0.0707 ± 0.0012 (clears) | = baseline, by construction | = baseline, by construction |
| L10.mlp | `direct_mean` | +2.077 ± 0.034 | 1 | +2.076 ± 0.034 | replicated | 0.1248 ± 0.0016 (clears) | +1.450 ± 0.029, same, clears | = baseline, by construction |
| L9.mlp | `direct_mean` | +1.631 ± 0.029 | 2 | +1.621 ± 0.029 | replicated | 0.0707 ± 0.0012 (clears) | +0.689 ± 0.023, same, clears | = baseline, by construction |
| L7H6 | `direct_mean` | +1.320 ± 0.028 | 3 | +1.264 ± 0.026 | replicated | −0.01027 ± 0.00064 (clears) | +0.846 ± 0.025, same, clears | = baseline, by construction |
| L10H7 | `direct_mean` | −1.254 ± 0.017 | 4 | −1.256 ± 0.018 | replicated | −0.0838 ± 0.0013 (clears) | −0.917 ± 0.018, same, clears | = baseline, by construction |
| L8H5 | `direct_mean` | +1.211 ± 0.025 | 5 | +1.205 ± 0.025 | replicated | 0.00225 ± 0.00031 (clears) | +0.700 ± 0.018, same, clears | = baseline, by construction |
| L11.mlp | `direct_mean` | +0.976 ± 0.045 | 6 | +0.998 ± 0.046 | replicated | 0.0960 ± 0.0025 (clears) | **−0.168 ± 0.041, flipped, clears** | = baseline, by construction |
| L11H10 | `direct_mean` | −0.889 ± 0.017 | 7 | −0.890 ± 0.016 | replicated | −0.04813 ± 0.00092 (clears) | −0.682 ± 0.016, same, clears | = baseline, by construction |
| L11H8 | `direct_mean` | +0.833 ± 0.022 | 8 | +0.800 ± 0.022 | replicated | 0.00901 ± 0.00047 (clears) | +0.545 ± 0.019, same, clears | = baseline, by construction |
| L8.mlp | `direct_mean` | +0.821 ± 0.023 | 9 | +0.767 ± 0.025 | replicated | 0.0489 ± 0.0010 (clears) | +0.639 ± 0.022, same, clears | = baseline, by construction |
| L7.mlp | `direct_mean` | +0.818 ± 0.026 | 10 | +0.786 ± 0.025 | replicated | 0.0435 ± 0.0010 (clears) | +0.602 ± 0.024, same, clears | = baseline, by construction |
| L10.mlp | `direct_resample` | +2.177 ± 0.036 | 1 | +2.158 ± 0.036 | replicated | 0.1248 ± 0.0016 (clears) | +1.598 ± 0.034, same, clears | = baseline, by construction |
| L9.mlp | `direct_resample` | +1.815 ± 0.033 | 2 | +1.796 ± 0.032 | replicated | 0.0707 ± 0.0012 (clears) | +0.831 ± 0.028, same, clears | = baseline, by construction |
| L7H6 | `direct_resample` | +1.318 ± 0.028 | 3 | +1.265 ± 0.026 | replicated | −0.01027 ± 0.00064 (clears) | +0.838 ± 0.025, same, clears | = baseline, by construction |
| L0.mlp | `direct_resample` | +1.260 ± 0.033 | 4 | +1.249 ± 0.032 | replicated | 0.9027 ± 0.0071 (clears) | +0.0153 ± 0.0036, same, clears | = baseline, by construction |
| L10H7 | `direct_resample` | −1.257 ± 0.017 | 5 | −1.256 ± 0.018 | replicated | −0.0838 ± 0.0013 (clears) | −0.888 ± 0.022, same, clears | = baseline, by construction |
| L8H5 | `direct_resample` | +1.212 ± 0.025 | 6 | +1.205 ± 0.025 | replicated | 0.00225 ± 0.00031 (clears) | +0.709 ± 0.019, same, clears | = baseline, by construction |
| L7.mlp | `direct_resample` | +1.066 ± 0.029 | 7 | +1.022 ± 0.029 | replicated | 0.0435 ± 0.0010 (clears) | +0.802 ± 0.027, same, clears | = baseline, by construction |
| L8.mlp | `direct_resample` | +1.049 ± 0.026 | 8 | +0.996 ± 0.028 | replicated | 0.0489 ± 0.0010 (clears) | +0.791 ± 0.024, same, clears | = baseline, by construction |
| L0H1 | `direct_resample` | +0.987 ± 0.028 | 9 | +1.000 ± 0.028 | replicated | 0.0013 ± 0.0016 (does not clear) | +0.0090 ± 0.0027, same, clears | = baseline, by construction |
| L11.mlp | `direct_resample` | +0.897 ± 0.056 | 10 | +0.936 ± 0.057 | replicated | 0.0960 ± 0.0025 (clears) | **−0.144 ± 0.050, flipped, clears** | = baseline, by construction |

Rule-1 sentences, one per replicated component; adversarial disagreements are
stated in the component's own paragraph (arms equal to baseline by
construction are not repeated here):

**L0.mlp** (7 cell sets, all replicated). Necessity: ablating L0.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +15.525 ± 0.166; mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +13.725 ± 0.142; resample, node, unfrozen [fraction removed 1.000]: +16.986 ± 0.138; zero, node, frozen: +3.370 ± 0.105; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.276 ± 0.110; resample, node, frozen [fraction removed 1.000]: +13.698 ± 0.141; resample, edge to logits, unfrozen [fraction removed 1.000]: +1.260 ± 0.033. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0.mlp's clean output into the corrupt run restores 0.9027 ± 0.0071 of the gap (clears Holm). Adversarial disagreement (selecting draw): under zero, node, frozen, the END-only arm gives −0.641 ± 0.027 against the all-position `fresh_prefix` baseline +3.370 (flipped, clears Holm); under mean, node, frozen, the END-only arm gives −0.473 ± 0.025 against the all-position `fresh_prefix` baseline +1.276 (flipped, clears Holm).

**L5H1** (6 cell sets, all replicated). Necessity: ablating L5H1 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +4.361 ± 0.075; mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +6.303 ± 0.086; resample, node, unfrozen [fraction removed 1.000]: +6.301 ± 0.086; zero, node, frozen: +2.932 ± 0.060; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +4.550 ± 0.074; resample, node, frozen [fraction removed 1.000]: +4.550 ± 0.074. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5H1's clean output into the corrupt run restores 0.0564 ± 0.0011 of the gap (clears Holm). Adversarial disagreement (selecting draw): under zero, node, frozen, the END-only arm gives −0.089 ± 0.021 against the all-position `fresh_prefix` baseline +2.932 (flipped, clears Holm).

**L7H6** (9 cell sets, all replicated). Necessity: ablating L7H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +3.202 ± 0.050; mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +1.992 ± 0.043; resample, node, unfrozen [fraction removed 1.000]: +2.012 ± 0.043; zero, node, frozen: +2.528 ± 0.041; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.742 ± 0.035; resample, node, frozen [fraction removed 1.000]: +1.740 ± 0.035; zero, edge to logits, unfrozen: +2.047 ± 0.033; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +1.320 ± 0.028; resample, edge to logits, unfrozen [fraction removed 1.000]: +1.318 ± 0.028. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L7H6's clean output into the corrupt run restores −0.01027 ± 0.00064 of the gap (clears Holm).

**L4H11** (3 cell sets, all replicated). Necessity: ablating L4H11 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +3.166 ± 0.061; mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +3.209 ± 0.061; resample, node, unfrozen [fraction removed 1.000]: +5.248 ± 0.082. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L4H11's clean output into the corrupt run restores 0.00028 ± 0.00053 of the gap (does not clear Holm).

**L0H1** (5 cell sets, all replicated). Necessity: ablating L0H1 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +3.096 ± 0.083; resample, node, unfrozen [fraction removed 1.000]: +2.771 ± 0.065; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.549 ± 0.036; resample, node, frozen [fraction removed 1.000]: +2.178 ± 0.049; resample, edge to logits, unfrozen [fraction removed 1.000]: +0.987 ± 0.028. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0H1's clean output into the corrupt run restores 0.0013 ± 0.0016 of the gap (does not clear Holm). Adversarial disagreement (selecting draw): under mean, node, frozen, the `shuffle_prefix` arm gives −0.076 ± 0.015 against the all-position `fresh_prefix` baseline +1.549 (flipped, clears Holm).

**L5H9** (2 cell sets, all replicated). Necessity: ablating L5H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +2.845 ± 0.052; zero, node, frozen: +1.464 ± 0.031. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5H9's clean output into the corrupt run restores −0.00034 ± 0.00051 of the gap (does not clear Holm).

**L0H3** (2 cell sets, all replicated). Necessity: ablating L0H3 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +2.251 ± 0.054; zero, node, frozen: +1.723 ± 0.044. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0H3's clean output into the corrupt run restores −0.00034 ± 0.00020 of the gap (does not clear Holm).

**L0H11** (2 cell sets, all replicated). Necessity: ablating L0H11 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: −2.028 ± 0.043; zero, node, frozen: −2.186 ± 0.030. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0H11's clean output into the corrupt run restores −0.00016 ± 0.00011 of the gap (does not clear Holm).

**L1H10** (1 cell set, replicated). Necessity: ablating L1H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +2.012 ± 0.056. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L1H10's clean output into the corrupt run restores −0.000033 ± 0.000049 of the gap (does not clear Holm).

**L11.mlp** (5 cell sets, all replicated). Necessity: ablating L11.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: −1.752 ± 0.045; zero, node, frozen: −1.752 ± 0.045; zero, edge to logits, unfrozen: −1.752 ± 0.045; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +0.976 ± 0.045; resample, edge to logits, unfrozen [fraction removed 1.000]: +0.897 ± 0.056. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11.mlp's clean output into the corrupt run restores 0.0960 ± 0.0025 of the gap (clears Holm). Adversarial disagreement (selecting draw): under mean, edge to logits, unfrozen, the `shuffle_prefix` arm gives −0.168 ± 0.041 against the all-position `fresh_prefix` baseline +0.976 (flipped, clears Holm); under resample, edge to logits, unfrozen, the `shuffle_prefix` arm gives −0.144 ± 0.050 against the all-position `fresh_prefix` baseline +0.897 (flipped, clears Holm).

**L4.mlp** (2 cell sets, all replicated). Necessity: ablating L4.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +2.201 ± 0.064; resample, node, unfrozen [fraction removed 1.000]: +2.067 ± 0.066. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L4.mlp's clean output into the corrupt run restores 0.00064 ± 0.00057 of the gap (does not clear Holm).

**L9.mlp** (7 cell sets, all replicated). Necessity: ablating L9.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +2.094 ± 0.043; resample, node, unfrozen [fraction removed 1.000]: +2.276 ± 0.047; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.916 ± 0.034; resample, node, frozen [fraction removed 1.000]: +2.104 ± 0.038; zero, edge to logits, unfrozen: +0.757 ± 0.025; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +1.631 ± 0.029; resample, edge to logits, unfrozen [fraction removed 1.000]: +1.815 ± 0.033. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9.mlp's clean output into the corrupt run restores 0.0707 ± 0.0012 of the gap (clears Holm).

**L10.mlp** (8 cell sets, all replicated). Necessity: ablating L10.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +2.090 ± 0.041; resample, node, unfrozen [fraction removed 1.000]: +2.192 ± 0.044; zero, node, frozen: +2.009 ± 0.034; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +2.204 ± 0.038; resample, node, frozen [fraction removed 1.000]: +2.318 ± 0.040; zero, edge to logits, unfrozen: +1.749 ± 0.032; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +2.077 ± 0.034; resample, edge to logits, unfrozen [fraction removed 1.000]: +2.177 ± 0.036. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10.mlp's clean output into the corrupt run restores 0.1248 ± 0.0016 of the gap (clears Holm).

**L8H5** (7 cell sets, all replicated). Necessity: ablating L8H5 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +2.075 ± 0.041; resample, node, unfrozen [fraction removed 1.000]: +2.063 ± 0.042; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.534 ± 0.031; resample, node, frozen [fraction removed 1.000]: +1.530 ± 0.032; zero, edge to logits, unfrozen: +0.782 ± 0.020; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +1.211 ± 0.025; resample, edge to logits, unfrozen [fraction removed 1.000]: +1.212 ± 0.025. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8H5's clean output into the corrupt run restores 0.00225 ± 0.00031 of the gap (clears Holm).

**L7.mlp** (7 cell sets, all replicated). Necessity: ablating L7.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +1.991 ± 0.053; resample, node, unfrozen [fraction removed 1.000]: +2.251 ± 0.057; zero, node, frozen: +1.385 ± 0.035; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.710 ± 0.039; resample, node, frozen [fraction removed 1.000]: +2.005 ± 0.043; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +0.818 ± 0.026; resample, edge to logits, unfrozen [fraction removed 1.000]: +1.066 ± 0.029. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L7.mlp's clean output into the corrupt run restores 0.0435 ± 0.0010 of the gap (clears Holm).

**L6H7** (1 cell set, replicated). Necessity: ablating L6H7 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +1.831 ± 0.037. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H7's clean output into the corrupt run restores 0.00031 ± 0.00038 of the gap (does not clear Holm).

**L6.mlp** (3 cell sets, all replicated). Necessity: ablating L6.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +1.557 ± 0.034; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.151 ± 0.030; resample, node, frozen [fraction removed 1.000]: +1.474 ± 0.033. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6.mlp's clean output into the corrupt run restores −0.00310 ± 0.00079 of the gap (clears Holm).

**L10H7** (4 cell sets, all replicated). Necessity: ablating L10H7 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, frozen [ref n 2,000; fraction removed 1.000]: −1.274 ± 0.017; zero, edge to logits, unfrozen: −0.900 ± 0.018; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: −1.254 ± 0.017; resample, edge to logits, unfrozen [fraction removed 1.000]: −1.257 ± 0.017. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H7's clean output into the corrupt run restores −0.0838 ± 0.0013 of the gap (clears Holm).

**L8.mlp** (3 cell sets, all replicated). Necessity: ablating L8.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, node, frozen [fraction removed 1.000]: +1.319 ± 0.031; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +0.821 ± 0.023; resample, edge to logits, unfrozen [fraction removed 1.000]: +1.049 ± 0.026. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8.mlp's clean output into the corrupt run restores 0.0489 ± 0.0010 of the gap (clears Holm).

**L6H9** (1 cell set, replicated). Necessity: ablating L6H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, edge to logits, unfrozen: −0.931 ± 0.024. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H9's clean output into the corrupt run restores 0.07682 ± 0.00094 of the gap (clears Holm).

**L11H0** (1 cell set, replicated). Necessity: ablating L11H0 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, edge to logits, unfrozen: +0.868 ± 0.041. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H0's clean output into the corrupt run restores −0.00006 ± 0.00020 of the gap (does not clear Holm).

**L9H6** (1 cell set, replicated). Necessity: ablating L9H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, edge to logits, unfrozen: +0.806 ± 0.016. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9H6's clean output into the corrupt run restores 0.0777 ± 0.0013 of the gap (clears Holm).

**L11H10** (2 cell sets, all replicated). Necessity: ablating L11H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, edge to logits, unfrozen: −0.797 ± 0.016; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: −0.889 ± 0.017. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H10's clean output into the corrupt run restores −0.04813 ± 0.00092 of the gap (clears Holm).

**L11H8** (1 cell set, replicated). Necessity: ablating L11H8 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +0.833 ± 0.022. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H8's clean output into the corrupt run restores 0.00901 ± 0.00047 of the gap (clears Holm).

**E2 I3's units** (not selections; run under all six total-effect maps as
pre-registered). Same columns and conventions:

| Unit | Cell set | Baseline (`fresh_prefix`, all positions) | `shuffle_prefix` arm | END-only arm |
|---|---|---|---|---|
| L5H5 | `total_zero_unfrozen` | +1.562 ± 0.038 | = baseline, by construction | +0.138 ± 0.017, same, clears |
| L5H5 | `total_mean_unfrozen` | +0.517 ± 0.030 | +0.456 ± 0.020, same, clears | +0.204 ± 0.021, same, clears |
| L5H5 | `total_resample_unfrozen` | +0.556 ± 0.031 | +0.781 ± 0.028, same, clears | +0.209 ± 0.021, same, clears |
| L5H5 | `total_zero_frozen` | −0.201 ± 0.021 | = baseline, by construction | −0.212 ± 0.012, same, clears |
| L5H5 | `total_mean_frozen` | +0.107 ± 0.018 | +0.223 ± 0.013, same, clears | **−0.140 ± 0.014, flipped, clears** |
| L5H5 | `total_resample_frozen` | +0.124 ± 0.018 | +0.379 ± 0.018, same, clears | **−0.130 ± 0.014, flipped, clears** |
| L6H9 | `total_zero_unfrozen` | +0.453 ± 0.027 | = baseline, by construction | +0.088 ± 0.024, same, clears |
| L6H9 | `total_mean_unfrozen` | +0.804 ± 0.029 | +1.159 ± 0.029, same, clears | +0.610 ± 0.026, same, clears |
| L6H9 | `total_resample_unfrozen` | +0.813 ± 0.030 | +1.615 ± 0.047, same, clears | +0.622 ± 0.026, same, clears |
| L6H9 | `total_zero_frozen` | −0.710 ± 0.023 | = baseline, by construction | −0.924 ± 0.025, same, clears |
| L6H9 | `total_mean_frozen` | −0.130 ± 0.019 | **+0.404 ± 0.020, flipped, clears** | −0.441 ± 0.021, same, clears |
| L6H9 | `total_resample_frozen` | −0.115 ± 0.020 | **+0.938 ± 0.036, flipped, clears** | −0.424 ± 0.022, same, clears |
| L4H11 | `total_zero_unfrozen` | +3.166 ± 0.061 | = baseline, by construction | +0.0771 ± 0.0087, same, clears |
| L4H11 | `total_mean_unfrozen` | +3.209 ± 0.061 | +2.993 ± 0.060, same, clears | +0.1506 ± 0.0085, same, clears |
| L4H11 | `total_resample_unfrozen` | +5.248 ± 0.082 | +4.938 ± 0.084, same, clears | +0.0966 ± 0.0059, same, clears |
| L4H11 | `total_zero_frozen` | −0.290 ± 0.014 | = baseline, by construction | −0.1145 ± 0.0044, same, clears |
| L4H11 | `total_mean_frozen` | −0.346 ± 0.012 | −0.543 ± 0.014, same, clears | −0.0545 ± 0.0040, same, clears |
| L4H11 | `total_resample_frozen` | +0.079 ± 0.014 | **−0.116 ± 0.013, flipped, clears** | **+0.0000 ± 0.0026, same, does not clear** |
| L2H2 | `total_zero_unfrozen` | +0.146 ± 0.019 | = baseline, by construction | **−0.0402 ± 0.0043, flipped, clears** |
| L2H2 | `total_mean_unfrozen` | +0.048 ± 0.018 | +0.103 ± 0.018, same, clears | **−0.0516 ± 0.0036, flipped, clears** |
| L2H2 | `total_resample_unfrozen` | +0.224 ± 0.019 | +0.314 ± 0.023, same, clears | **−0.0281 ± 0.0022, flipped, clears** |
| L2H2 | `total_zero_frozen` | −0.2233 ± 0.0076 | = baseline, by construction | −0.0557 ± 0.0021, same, clears |
| L2H2 | `total_mean_frozen` | −0.2496 ± 0.0076 | −0.1870 ± 0.0065, same, clears | −0.0843 ± 0.0024, same, clears |
| L2H2 | `total_resample_frozen` | −0.0876 ± 0.0075 | −0.0210 ± 0.0069, same, clears | −0.0429 ± 0.0013, same, clears |
| L5H5, L6H9 | `total_zero_unfrozen` | +2.581 ± 0.054 | = baseline, by construction | +0.544 ± 0.040, same, clears |
| L5H5, L6H9 | `total_mean_unfrozen` | +2.880 ± 0.065 | +2.068 ± 0.050, same, clears | +1.851 ± 0.053, same, clears |
| L5H5, L6H9 | `total_resample_unfrozen` | +2.943 ± 0.066 | +3.169 ± 0.085, same, clears | +1.885 ± 0.055, same, clears |
| L5H5, L6H9 | `total_zero_frozen` | −0.648 ± 0.036 | = baseline, by construction | −1.118 ± 0.036, same, clears |
| L5H5, L6H9 | `total_mean_frozen` | +1.046 ± 0.040 | +0.849 ± 0.036, same, clears | **−0.131 ± 0.036, flipped, clears** |
| L5H5, L6H9 | `total_resample_frozen` | +1.091 ± 0.041 | +1.717 ± 0.057, same, clears | **−0.097 ± 0.037, flipped, clears** |

The pre-registration stated that the previous-token heads `L4H11` and `L2H2`
(4.11 and 2.2) act at B1, not END (E2 I4), so a small END-only effect for
them is expected and is not a refutation. Under that statement: the one arm
of all 250 that does not clear Holm is `L4H11`'s END-only arm under
resample, frozen (+0.00005 ± 0.0026 against a baseline of +0.079), and
`L2H2`'s END-only arm flips sign under all three unfrozen values (−0.040,
−0.052 and −0.028 against +0.146, +0.048 and +0.224). No expectation was
stated for the other E2 I3 flips: under mean and resample, frozen, the END-only
arm raises the mean `ld` for `L5H5` (−0.140 ± 0.014 and −0.130 ± 0.014
against +0.107 and +0.124) and for the set {`L5H5`, `L6H9`} (−0.131 ± 0.036
and −0.097 ± 0.037 against +1.046 and +1.091); the `shuffle_prefix` arm
lowers it for `L6H9` (+0.404 ± 0.020 and +0.938 ± 0.036 against −0.130 and
−0.115) and raises it for `L4H11` under resample, frozen (−0.116 ± 0.013
against +0.079). The flips among the selections are stated in their
components' paragraphs above and in the exploratory section.

**Adversarial counts.** 125 units: 30 from E2 I3 (5 units × 6 maps), 90
confirmatory and 9 exploratory induction selections, with 4 shared between
the sources. 250 tested arms (125 × `shuffle_prefix` and END-only); 249 clear
Holm in `adversarial`. Of the 250, 73 are uninformative by construction (39
`shuffle_prefix` under zero, 32 END-only on direct maps, 2 END-only on
`L11.mlp`). Of the 177 informative arms (250 − 73), **158 held up** (same
sign as the baseline and clear Holm: 78 of 86 informative `shuffle_prefix`
arms, 80 of 91 informative END-only arms), **18 flip sign** against the
baseline (8 `shuffle_prefix`, 10 END-only; all 18 clear Holm), and 1 keeps
the sign but does not clear (the `L4H11` arm above).

#### Agreement (confirmatory)

| Component | Cell set | Seed 0 effect ± s | Rank | Held-out effect ± s | Verdict | Restored ± sem (Holm) |
|---|---|---|---|---|---|---|
| L0.mlp | `total_zero_unfrozen` | +1.877 ± 0.032 | 1 | +1.912 ± 0.032 | replicated | 0.9846 ± 0.0078 (clears) |
| L0H9 | `total_zero_unfrozen` | +0.771 ± 0.031 | 2 | +0.816 ± 0.032 | replicated | 0.000448 ± 0.000078 (clears) |
| L10.mlp | `total_zero_unfrozen` | +0.767 ± 0.012 | 3 | +0.768 ± 0.012 | replicated | 0.3186 ± 0.0040 (clears) |
| L11.mlp | `total_zero_unfrozen` | +0.6325 ± 0.0100 | 4 | +0.6469 ± 0.0098 | replicated | 0.2885 ± 0.0024 (clears) |
| L8H5 | `total_zero_unfrozen` | +0.577 ± 0.012 | 5 | +0.576 ± 0.012 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `total_zero_unfrozen` | +0.537 ± 0.010 | 6 | +0.5334 ± 0.0099 | replicated | 0.2598 ± 0.0031 (clears) |
| L5H9 | `total_zero_unfrozen` | +0.5286 ± 0.0080 | 7 | +0.5324 ± 0.0082 | replicated | 0.00018 ± 0.00014 (does not clear) |
| L6H0 | `total_zero_unfrozen` | +0.3790 ± 0.0053 | 8 | +0.3825 ± 0.0053 | replicated | 0.1326 ± 0.0015 (clears) |
| L0H8 | `total_zero_unfrozen` | −0.374 ± 0.011 | 9 | −0.397 ± 0.012 | replicated | −0.00007 ± 0.00011 (does not clear) |
| L6.mlp | `total_zero_unfrozen` | −0.3531 ± 0.0094 | 10 | −0.3732 ± 0.0094 | replicated | 0.0313 ± 0.0013 (clears) |
| L0.mlp | `total_mean_unfrozen` | +1.077 ± 0.054 | 1 | +1.131 ± 0.054 | replicated | 0.9846 ± 0.0078 (clears) |
| L10.mlp | `total_mean_unfrozen` | +0.746 ± 0.014 | 2 | +0.746 ± 0.015 | replicated | 0.3186 ± 0.0040 (clears) |
| L11.mlp | `total_mean_unfrozen` | +0.7143 ± 0.0087 | 3 | +0.7278 ± 0.0089 | replicated | 0.2885 ± 0.0024 (clears) |
| L8H5 | `total_mean_unfrozen` | +0.6578 ± 0.0062 | 4 | +0.6618 ± 0.0064 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `total_mean_unfrozen` | +0.5929 ± 0.0082 | 5 | +0.5916 ± 0.0081 | replicated | 0.2598 ± 0.0031 (clears) |
| L10H9 | `total_mean_unfrozen` | +0.3644 ± 0.0053 | 6 | +0.3636 ± 0.0052 | replicated | 0.1590 ± 0.0021 (clears) |
| L9.mlp | `total_mean_unfrozen` | +0.327 ± 0.010 | 7 | +0.326 ± 0.010 | replicated | 0.1756 ± 0.0026 (clears) |
| L6H0 | `total_mean_unfrozen` | +0.2840 ± 0.0040 | 8 | +0.2905 ± 0.0040 | replicated | 0.1326 ± 0.0015 (clears) |
| L8.mlp | `total_mean_unfrozen` | +0.273 ± 0.025 | 9 | +0.283 ± 0.025 | replicated | 0.0925 ± 0.0019 (clears) |
| L10H5 | `total_mean_unfrozen` | +0.1643 ± 0.0028 | 10 | +0.1694 ± 0.0029 | replicated | 0.07310 ± 0.00092 (clears) |
| L0.mlp | `total_resample_unfrozen` | +5.064 ± 0.040 | 1 | +5.086 ± 0.040 | replicated | 0.9846 ± 0.0078 (clears) |
| L10.mlp | `total_resample_unfrozen` | +1.628 ± 0.020 | 2 | +1.646 ± 0.021 | replicated | 0.3186 ± 0.0040 (clears) |
| L8H5 | `total_resample_unfrozen` | +1.475 ± 0.011 | 3 | +1.490 ± 0.012 | replicated | 0.2859 ± 0.0023 (clears) |
| L11.mlp | `total_resample_unfrozen` | +1.450 ± 0.012 | 4 | +1.486 ± 0.012 | replicated | 0.2885 ± 0.0024 (clears) |
| L7H4 | `total_resample_unfrozen` | +1.358 ± 0.016 | 5 | +1.361 ± 0.017 | replicated | 0.2598 ± 0.0031 (clears) |
| L9.mlp | `total_resample_unfrozen` | +0.897 ± 0.014 | 6 | +0.905 ± 0.014 | replicated | 0.1756 ± 0.0026 (clears) |
| L10H9 | `total_resample_unfrozen` | +0.816 ± 0.011 | 7 | +0.823 ± 0.011 | replicated | 0.1590 ± 0.0021 (clears) |
| L6H0 | `total_resample_unfrozen` | +0.6750 ± 0.0076 | 8 | +0.6920 ± 0.0080 | replicated | 0.1326 ± 0.0015 (clears) |
| L8.mlp | `total_resample_unfrozen` | +0.4755 ± 0.0100 | 9 | +0.4898 ± 0.0099 | replicated | 0.0925 ± 0.0019 (clears) |
| L5H2 | `total_resample_unfrozen` | +0.3876 ± 0.0049 | 10 | +0.3890 ± 0.0049 | replicated | 0.07452 ± 0.00095 (clears) |
| L10.mlp | `total_zero_frozen` | +0.658 ± 0.011 | 1 | +0.658 ± 0.011 | replicated | 0.3186 ± 0.0040 (clears) |
| L0H9 | `total_zero_frozen` | +0.644 ± 0.021 | 2 | +0.677 ± 0.021 | replicated | 0.000448 ± 0.000078 (clears) |
| L11.mlp | `total_zero_frozen` | +0.6325 ± 0.0100 | 3 | +0.6469 ± 0.0098 | replicated | 0.2885 ± 0.0024 (clears) |
| L8H5 | `total_zero_frozen` | +0.610 ± 0.012 | 4 | +0.608 ± 0.012 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `total_zero_frozen` | +0.589 ± 0.010 | 5 | +0.585 ± 0.010 | replicated | 0.2598 ± 0.0031 (clears) |
| L6H0 | `total_zero_frozen` | +0.3888 ± 0.0053 | 6 | +0.3931 ± 0.0053 | replicated | 0.1326 ± 0.0015 (clears) |
| L5H9 | `total_zero_frozen` | +0.3549 ± 0.0063 | 7 | +0.3561 ± 0.0063 | replicated | 0.00018 ± 0.00014 (does not clear) |
| L6.mlp | `total_zero_frozen` | −0.3380 ± 0.0072 | 8 | −0.3474 ± 0.0072 | replicated | 0.0313 ± 0.0013 (clears) |
| L5H2 | `total_zero_frozen` | +0.3244 ± 0.0046 | 9 | +0.3230 ± 0.0045 | replicated | 0.07452 ± 0.00095 (clears) |
| L2H8 | `total_zero_frozen` | +0.3241 ± 0.0084 | 10 | +0.3197 ± 0.0085 | replicated | 0.000980 ± 0.000095 (clears) |
| L10.mlp | `total_mean_frozen` | +0.741 ± 0.014 | 1 | +0.743 ± 0.015 | replicated | 0.3186 ± 0.0040 (clears) |
| L11.mlp | `total_mean_frozen` | +0.7143 ± 0.0087 | 2 | +0.7278 ± 0.0089 | replicated | 0.2885 ± 0.0024 (clears) |
| L8H5 | `total_mean_frozen` | +0.6530 ± 0.0062 | 3 | +0.6565 ± 0.0063 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `total_mean_frozen` | +0.5847 ± 0.0087 | 4 | +0.5828 ± 0.0085 | replicated | 0.2598 ± 0.0031 (clears) |
| L0.mlp | `total_mean_frozen` | +0.436 ± 0.037 | 5 | +0.495 ± 0.038 | replicated | 0.9846 ± 0.0078 (clears) |
| L10H9 | `total_mean_frozen` | +0.3652 ± 0.0053 | 6 | +0.3641 ± 0.0052 | replicated | 0.1590 ± 0.0021 (clears) |
| L9.mlp | `total_mean_frozen` | +0.3241 ± 0.0097 | 7 | +0.3278 ± 0.0096 | replicated | 0.1756 ± 0.0026 (clears) |
| L6H0 | `total_mean_frozen` | +0.3092 ± 0.0039 | 8 | +0.3161 ± 0.0039 | replicated | 0.1326 ± 0.0015 (clears) |
| L8.mlp | `total_mean_frozen` | +0.279 ± 0.025 | 9 | +0.290 ± 0.025 | replicated | 0.0925 ± 0.0019 (clears) |
| L5H2 | `total_mean_frozen` | +0.1773 ± 0.0027 | 10 | +0.1768 ± 0.0027 | replicated | 0.07452 ± 0.00095 (clears) |
| L0.mlp | `total_resample_frozen` | +4.982 ± 0.040 | 1 | +5.005 ± 0.040 | replicated | 0.9846 ± 0.0078 (clears) |
| L10.mlp | `total_resample_frozen` | +1.616 ± 0.020 | 2 | +1.635 ± 0.021 | replicated | 0.3186 ± 0.0040 (clears) |
| L8H5 | `total_resample_frozen` | +1.470 ± 0.011 | 3 | +1.484 ± 0.012 | replicated | 0.2859 ± 0.0023 (clears) |
| L11.mlp | `total_resample_frozen` | +1.450 ± 0.012 | 4 | +1.486 ± 0.012 | replicated | 0.2885 ± 0.0024 (clears) |
| L7H4 | `total_resample_frozen` | +1.348 ± 0.016 | 5 | +1.349 ± 0.016 | replicated | 0.2598 ± 0.0031 (clears) |
| L9.mlp | `total_resample_frozen` | +0.881 ± 0.013 | 6 | +0.891 ± 0.013 | replicated | 0.1756 ± 0.0026 (clears) |
| L10H9 | `total_resample_frozen` | +0.817 ± 0.011 | 7 | +0.824 ± 0.011 | replicated | 0.1590 ± 0.0021 (clears) |
| L6H0 | `total_resample_frozen` | +0.7030 ± 0.0074 | 8 | +0.7198 ± 0.0077 | replicated | 0.1326 ± 0.0015 (clears) |
| L8.mlp | `total_resample_frozen` | +0.4607 ± 0.0097 | 9 | +0.4747 ± 0.0096 | replicated | 0.0925 ± 0.0019 (clears) |
| L4H3 | `total_resample_frozen` | +0.4138 ± 0.0060 | 10 | +0.4219 ± 0.0064 | replicated | 0.0738 ± 0.0012 (clears) |
| L0.mlp | `direct_zero` | −0.822 ± 0.018 | 1 | −0.824 ± 0.018 | replicated | 0.9846 ± 0.0078 (clears) |
| L11.mlp | `direct_zero` | +0.6325 ± 0.0100 | 2 | +0.6469 ± 0.0098 | replicated | 0.2885 ± 0.0024 (clears) |
| L10.mlp | `direct_zero` | +0.563 ± 0.010 | 3 | +0.561 ± 0.011 | replicated | 0.3186 ± 0.0040 (clears) |
| L8H5 | `direct_zero` | +0.5051 ± 0.0099 | 4 | +0.5030 ± 0.0097 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `direct_zero` | +0.4936 ± 0.0078 | 5 | +0.4906 ± 0.0077 | replicated | 0.2598 ± 0.0031 (clears) |
| L6.mlp | `direct_zero` | −0.3066 ± 0.0058 | 6 | −0.3176 ± 0.0060 | replicated | 0.0313 ± 0.0013 (clears) |
| L8.mlp | `direct_zero` | +0.242 ± 0.025 | 7 | +0.250 ± 0.025 | replicated | 0.0925 ± 0.0019 (clears) |
| L11H8 | `direct_zero` | −0.2014 ± 0.0045 | 8 | −0.1980 ± 0.0045 | replicated | 0.00201 ± 0.00014 (clears) |
| L6H0 | `direct_zero` | +0.2014 ± 0.0032 | 9 | +0.2060 ± 0.0032 | replicated | 0.1326 ± 0.0015 (clears) |
| L5.mlp | `direct_zero` | −0.1889 ± 0.0061 | 10 | −0.1905 ± 0.0060 | replicated | 0.0354 ± 0.0012 (clears) |
| L10.mlp | `direct_mean` | +0.715 ± 0.014 | 1 | +0.716 ± 0.014 | replicated | 0.3186 ± 0.0040 (clears) |
| L11.mlp | `direct_mean` | +0.7143 ± 0.0087 | 2 | +0.7278 ± 0.0089 | replicated | 0.2885 ± 0.0024 (clears) |
| L8H5 | `direct_mean` | +0.5583 ± 0.0054 | 3 | +0.5603 ± 0.0054 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `direct_mean` | +0.5046 ± 0.0074 | 4 | +0.5041 ± 0.0073 | replicated | 0.2598 ± 0.0031 (clears) |
| L0.mlp | `direct_mean` | −0.472 ± 0.012 | 5 | −0.471 ± 0.012 | replicated | 0.9846 ± 0.0078 (clears) |
| L10H9 | `direct_mean` | +0.3577 ± 0.0052 | 6 | +0.3566 ± 0.0051 | replicated | 0.1590 ± 0.0021 (clears) |
| L9.mlp | `direct_mean` | +0.2044 ± 0.0079 | 7 | +0.2072 ± 0.0080 | replicated | 0.1756 ± 0.0026 (clears) |
| L8.mlp | `direct_mean` | +0.186 ± 0.022 | 8 | +0.194 ± 0.022 | replicated | 0.0925 ± 0.0019 (clears) |
| L5.mlp | `direct_mean` | −0.1723 ± 0.0046 | 9 | −0.1762 ± 0.0045 | replicated | 0.0354 ± 0.0012 (clears) |
| L6H0 | `direct_mean` | +0.1677 ± 0.0027 | 10 | +0.1723 ± 0.0027 | replicated | 0.1326 ± 0.0015 (clears) |
| L10.mlp | `direct_resample` | +1.562 ± 0.019 | 1 | +1.579 ± 0.020 | replicated | 0.3186 ± 0.0040 (clears) |
| L11.mlp | `direct_resample` | +1.450 ± 0.012 | 2 | +1.486 ± 0.012 | replicated | 0.2885 ± 0.0024 (clears) |
| L8H5 | `direct_resample` | +1.2498 ± 0.0098 | 3 | +1.260 ± 0.010 | replicated | 0.2859 ± 0.0023 (clears) |
| L7H4 | `direct_resample` | +1.167 ± 0.014 | 4 | +1.168 ± 0.014 | replicated | 0.2598 ± 0.0031 (clears) |
| L10H9 | `direct_resample` | +0.801 ± 0.011 | 5 | +0.808 ± 0.011 | replicated | 0.1590 ± 0.0021 (clears) |
| L9.mlp | `direct_resample` | +0.5937 ± 0.0085 | 6 | +0.5984 ± 0.0084 | replicated | 0.1756 ± 0.0026 (clears) |
| L6H0 | `direct_resample` | +0.3657 ± 0.0046 | 7 | +0.3756 ± 0.0047 | replicated | 0.1326 ± 0.0015 (clears) |
| L10H5 | `direct_resample` | +0.3540 ± 0.0042 | 8 | +0.3607 ± 0.0045 | replicated | 0.07310 ± 0.00092 (clears) |
| L8.mlp | `direct_resample` | +0.2692 ± 0.0065 | 9 | +0.2789 ± 0.0065 | replicated | 0.0925 ± 0.0019 (clears) |
| L11H10 | `direct_resample` | +0.2660 ± 0.0044 | 10 | +0.2708 ± 0.0043 | replicated | 0.05210 ± 0.00082 (clears) |

Rule-1 sentences, one per replicated component (agreement is ours and
unsourced; its mean reference mixes subject numbers, §3):

**L0.mlp** (7 cell sets, all replicated). Necessity: ablating L0.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +1.877 ± 0.032; mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +1.077 ± 0.054; resample, node, unfrozen [fraction removed 2.002]: +5.064 ± 0.040; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.436 ± 0.037; resample, node, frozen [fraction removed 2.002]: +4.982 ± 0.040; zero, edge to logits, unfrozen: −0.822 ± 0.018; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: −0.472 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0.mlp's clean output into the corrupt run restores 0.9846 ± 0.0078 of the gap (clears Holm).

**L0H9** (2 cell sets, all replicated). Necessity: ablating L0H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.771 ± 0.031; zero, node, frozen: +0.644 ± 0.021. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0H9's clean output into the corrupt run restores 0.000448 ± 0.000078 of the gap (clears Holm).

**L10.mlp** (9 cell sets, all replicated). Necessity: ablating L10.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.767 ± 0.012; mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.746 ± 0.014; resample, node, unfrozen [fraction removed 2.002]: +1.628 ± 0.020; zero, node, frozen: +0.658 ± 0.011; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.741 ± 0.014; resample, node, frozen [fraction removed 2.002]: +1.616 ± 0.020; zero, edge to logits, unfrozen: +0.563 ± 0.010; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.715 ± 0.014; resample, edge to logits, unfrozen [fraction removed 2.002]: +1.562 ± 0.019. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10.mlp's clean output into the corrupt run restores 0.3186 ± 0.0040 of the gap (clears Holm).

**L11.mlp** (9 cell sets, all replicated). Necessity: ablating L11.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.6325 ± 0.0100; mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.7143 ± 0.0087; resample, node, unfrozen [fraction removed 2.002]: +1.450 ± 0.012; zero, node, frozen: +0.6325 ± 0.0100; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.7143 ± 0.0087; resample, node, frozen [fraction removed 2.002]: +1.450 ± 0.012; zero, edge to logits, unfrozen: +0.6325 ± 0.0100; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.7143 ± 0.0087; resample, edge to logits, unfrozen [fraction removed 2.002]: +1.450 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11.mlp's clean output into the corrupt run restores 0.2885 ± 0.0024 of the gap (clears Holm).

**L8H5** (9 cell sets, all replicated). Necessity: ablating L8H5 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.577 ± 0.012; mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.6578 ± 0.0062; resample, node, unfrozen [fraction removed 2.002]: +1.475 ± 0.011; zero, node, frozen: +0.610 ± 0.012; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.6530 ± 0.0062; resample, node, frozen [fraction removed 2.002]: +1.470 ± 0.011; zero, edge to logits, unfrozen: +0.5051 ± 0.0099; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.5583 ± 0.0054; resample, edge to logits, unfrozen [fraction removed 2.002]: +1.2498 ± 0.0098. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8H5's clean output into the corrupt run restores 0.2859 ± 0.0023 of the gap (clears Holm).

**L7H4** (9 cell sets, all replicated). Necessity: ablating L7H4 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.537 ± 0.010; mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.5929 ± 0.0082; resample, node, unfrozen [fraction removed 2.002]: +1.358 ± 0.016; zero, node, frozen: +0.589 ± 0.010; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.5847 ± 0.0087; resample, node, frozen [fraction removed 2.002]: +1.348 ± 0.016; zero, edge to logits, unfrozen: +0.4936 ± 0.0078; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.5046 ± 0.0074; resample, edge to logits, unfrozen [fraction removed 2.002]: +1.167 ± 0.014. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L7H4's clean output into the corrupt run restores 0.2598 ± 0.0031 of the gap (clears Holm).

**L5H9** (2 cell sets, all replicated). Necessity: ablating L5H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.5286 ± 0.0080; zero, node, frozen: +0.3549 ± 0.0063. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5H9's clean output into the corrupt run restores 0.00018 ± 0.00014 of the gap (does not clear Holm).

**L6H0** (9 cell sets, all replicated). Necessity: ablating L6H0 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: +0.3790 ± 0.0053; mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.2840 ± 0.0040; resample, node, unfrozen [fraction removed 2.002]: +0.6750 ± 0.0076; zero, node, frozen: +0.3888 ± 0.0053; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.3092 ± 0.0039; resample, node, frozen [fraction removed 2.002]: +0.7030 ± 0.0074; zero, edge to logits, unfrozen: +0.2014 ± 0.0032; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.1677 ± 0.0027; resample, edge to logits, unfrozen [fraction removed 2.002]: +0.3657 ± 0.0046. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H0's clean output into the corrupt run restores 0.1326 ± 0.0015 of the gap (clears Holm).

**L0H8** (1 cell set, replicated). Necessity: ablating L0H8 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: −0.374 ± 0.011. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L0H8's clean output into the corrupt run restores −0.00007 ± 0.00011 of the gap (does not clear Holm).

**L6.mlp** (3 cell sets, all replicated). Necessity: ablating L6.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, unfrozen: −0.3531 ± 0.0094; zero, node, frozen: −0.3380 ± 0.0072; zero, edge to logits, unfrozen: −0.3066 ± 0.0058. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6.mlp's clean output into the corrupt run restores 0.0313 ± 0.0013 of the gap (clears Holm).

**L10H9** (6 cell sets, all replicated). Necessity: ablating L10H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.3644 ± 0.0053; resample, node, unfrozen [fraction removed 2.002]: +0.816 ± 0.011; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.3652 ± 0.0053; resample, node, frozen [fraction removed 2.002]: +0.817 ± 0.011; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.3577 ± 0.0052; resample, edge to logits, unfrozen [fraction removed 2.002]: +0.801 ± 0.011. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H9's clean output into the corrupt run restores 0.1590 ± 0.0021 of the gap (clears Holm).

**L9.mlp** (6 cell sets, all replicated). Necessity: ablating L9.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.327 ± 0.010; resample, node, unfrozen [fraction removed 2.002]: +0.897 ± 0.014; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.3241 ± 0.0097; resample, node, frozen [fraction removed 2.002]: +0.881 ± 0.013; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.2044 ± 0.0079; resample, edge to logits, unfrozen [fraction removed 2.002]: +0.5937 ± 0.0085. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9.mlp's clean output into the corrupt run restores 0.1756 ± 0.0026 of the gap (clears Holm).

**L8.mlp** (7 cell sets, all replicated). Necessity: ablating L8.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.273 ± 0.025; resample, node, unfrozen [fraction removed 2.002]: +0.4755 ± 0.0100; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.279 ± 0.025; resample, node, frozen [fraction removed 2.002]: +0.4607 ± 0.0097; zero, edge to logits, unfrozen: +0.242 ± 0.025; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: +0.186 ± 0.022; resample, edge to logits, unfrozen [fraction removed 2.002]: +0.2692 ± 0.0065. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8.mlp's clean output into the corrupt run restores 0.0925 ± 0.0019 of the gap (clears Holm).

**L10H5** (2 cell sets, all replicated). Necessity: ablating L10H5 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: +0.1643 ± 0.0028; resample, edge to logits, unfrozen [fraction removed 2.002]: +0.3540 ± 0.0042. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H5's clean output into the corrupt run restores 0.07310 ± 0.00092 of the gap (clears Holm).

**L5H2** (3 cell sets, all replicated). Necessity: ablating L5H2 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, node, unfrozen [fraction removed 2.002]: +0.3876 ± 0.0049; zero, node, frozen: +0.3244 ± 0.0046; mean, node, frozen [ref n 2,000; fraction removed 2.002]: +0.1773 ± 0.0027. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5H2's clean output into the corrupt run restores 0.07452 ± 0.00095 of the gap (clears Holm).

**L2H8** (1 cell set, replicated). Necessity: ablating L2H8 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, node, frozen: +0.3241 ± 0.0084. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L2H8's clean output into the corrupt run restores 0.000980 ± 0.000095 of the gap (clears Holm).

**L4H3** (1 cell set, replicated). Necessity: ablating L4H3 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, node, frozen [fraction removed 2.002]: +0.4138 ± 0.0060. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L4H3's clean output into the corrupt run restores 0.0738 ± 0.0012 of the gap (clears Holm).

**L11H8** (1 cell set, replicated). Necessity: ablating L11H8 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, edge to logits, unfrozen: −0.2014 ± 0.0045. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H8's clean output into the corrupt run restores 0.00201 ± 0.00014 of the gap (clears Holm).

**L5.mlp** (2 cell sets, all replicated). Necessity: ablating L5.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under zero, edge to logits, unfrozen: −0.1889 ± 0.0061; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 2.002]: −0.1723 ± 0.0046. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5.mlp's clean output into the corrupt run restores 0.0354 ± 0.0012 of the gap (clears Holm).

**L11H10** (1 cell set, replicated). Necessity: ablating L11H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, edge to logits, unfrozen [fraction removed 2.002]: +0.2660 ± 0.0044. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L11H10's clean output into the corrupt run restores 0.05210 ± 0.00082 of the gap (clears Holm).

#### Set restores (confirmatory)

Per item, the list's replicated heads together, restore-clean on the held-out
draw (sufficiency, `sufficiency_confirmatory`). MLPs are left out of the set
(the set machinery is heads only), and the ones left out are named:

- ioi: L0H8, L1H3, L3H0, L5H5, L5H9, L7H3, L7H9, L8H6, L8H10, L9H6, L9H9, L10H0, L10H6, L10H7, L10H10, L11H0, L11H2, L11H10 together restore 0.868 ± 0.011 of the gap (clears Holm); MLPs left out: L0.mlp, L4.mlp, L5.mlp, L10.mlp.
- induction: L0H1, L0H3, L0H11, L1H10, L4H11, L5H1, L5H9, L6H7, L6H9, L7H6, L8H5, L9H6, L10H7, L11H0, L11H8, L11H10 together restore 0.2847 ± 0.0058 of the gap (clears Holm); MLPs left out: L0.mlp, L4.mlp, L6.mlp, L7.mlp, L8.mlp, L9.mlp, L10.mlp, L11.mlp.
- agreement: L0H8, L0H9, L2H8, L4H3, L5H2, L5H9, L6H0, L7H4, L8H5, L10H5, L10H9, L11H8, L11H10 together restore 0.9876 ± 0.0077 of the gap (clears Holm); MLPs left out: L0.mlp, L5.mlp, L6.mlp, L8.mlp, L9.mlp, L10.mlp, L11.mlp.

### Exploratory (the author's list, labelled exploratory everywhere)

18 entries, chosen by the author after seeing the maps and committed before
their verification (`7738b51`); verified exactly as the confirmatory list.
**18 replicated**, 0 not replicated. Held-out / seed-0 effect ratio: 0.833 to
1.152. Restore: 12 of the 14 (item, component) singles clear Holm in
`sufficiency_exploratory`; 2 do not (§6). The author's reasons, verbatim from
`selection/exploratory.json` (`why`):

1. ioi / `total_mean_unfrozen` / L9H9: Frozen +2.580 (selected, rank 1) against unfrozen +0.260 under mean; zero +2.582 against +0.199, resample +2.596 against +0.306; direct +2.505. Delta (frozen − unfrozen) +2.320, the largest on IOI under mean. The unfrozen end is not selected in any set; listed so that the low end of the contrast is verified.
2. ioi / `total_mean_unfrozen` / L10H0: Frozen +0.754 (selected, rank 6) against unfrozen +0.395 under mean; zero +0.724 against +0.393, resample +0.771 against +0.404; direct +0.722. Delta +0.360. The unfrozen end is rank 12 under mean and not selected in any set.
3. ioi / `total_mean_unfrozen` / L8.mlp: Unfrozen negative under every value (zero −0.408, mean −0.385, resample −0.330). Frozen −0.381 under zero, +0.035 under mean, +0.061 under resample; direct −0.253 under zero, −0.005 under mean, +0.004 under resample (the last two not distinguishable from zero at this n). Delta +0.420 mean, +0.391 resample. Not selected in any set; no MLP with a negative effect is selected in any IOI total set.
4. ioi / `total_resample_unfrozen` / L4H11: Unfrozen +0.462 under resample (rank 11, one outside the cut), +0.279 under zero, +0.189 under mean. Frozen and direct within ±0.020 under every value. Delta −0.470 resample. Not selected in any set.
5. ioi / `total_mean_unfrozen` / L10H10: Frozen +0.465 (selected, rank 7) against unfrozen +0.134 under mean; zero +0.471 against +0.158, resample +0.476 against +0.137; direct +0.453. Delta +0.331. The unfrozen end is not selected in any set.
6. ioi / `total_mean_unfrozen` / L3.mlp: Under mean, frozen +0.164 (rank 18) and unfrozen −0.220 have opposite signs; direct −0.001 (not distinguishable from zero at this n); delta +0.384. Under resample, frozen +0.178 and unfrozen −0.027 (not distinguishable from zero at this n); under zero, +0.085 and +0.191. Neither end is selected in any set.
7. ioi / `total_mean_frozen` / L3.mlp: Frozen end of the L3.mlp pair (+0.164 under mean, rank 18), listed so that both ends of the sign difference are verified.
8. induction / `total_mean_unfrozen` / L6H6: Under mean: direct +0.257, frozen −0.239, unfrozen −1.343. Delta +1.103 mean, +1.133 resample, +0.619 zero. Frozen changes sign with the value: +0.879 zero, −0.239 mean, −0.258 resample. Not selected in any set.
9. induction / `total_mean_unfrozen` / L1.mlp: Direct −0.167 zero, −0.143 mean, +0.044 resample. Mean against resample: frozen −0.368 against +0.747, unfrozen −0.913 against +0.649. Not selected in any set.
10. induction / `total_resample_unfrozen` / L1.mlp: Resample end of the L1.mlp pair: direct +0.044, frozen +0.747, unfrozen +0.649 (rank 27); listed so that both signs are verified.
11. induction / `total_mean_unfrozen` / L7H3: On induction under mean: direct −0.356, frozen −0.627, unfrozen −1.230; resample within 0.003 of each. On IOI under mean: direct +0.054, frozen +0.053, unfrozen +0.515 (selected). The unfrozen effect has opposite signs on the two items. Not selected in any induction set.
12. induction / `direct_mean` / L9H6: Direct +0.805 (rank 11, one outside the cut), frozen +0.859, unfrozen −0.106 under mean; resample direct +0.818, unfrozen −0.094. Delta +0.965 mean. On IOI under mean: direct +0.944 (selected), unfrozen −0.457 (selected), delta +1.434.
13. induction / `direct_mean` / L6H9: Direct −0.477, frozen −0.130, unfrozen +0.804 under mean; direct and unfrozen have opposite signs under every value (zero −0.931, selected, against +0.453; resample −0.461 against +0.813). Delta −0.934 mean. On IOI under mean: direct −0.001, unfrozen +0.437.
14. induction / `total_mean_unfrozen` / L6H9: Unfrozen end of the L6H9 pair (+0.804 under mean, rank 24), listed so that both ends of the sign difference are verified.
15. induction / `total_mean_frozen` / L6H10: Frozen +1.037 (rank 12) against unfrozen −0.496 under mean, direct +0.496; resample +1.046 against −0.483; zero +0.445 against −0.605. Delta +1.533 mean, +1.529 resample, +1.050 zero. Not selected in any set. Every IOI L6H10 direct, frozen and unfrozen cell is within ±0.024.
16. induction / `total_mean_unfrozen` / L6H10: Unfrozen end of the L6H10 pair (−0.496 under mean, rank 32), listed so that both ends of the sign difference are verified.
17. agreement / `total_mean_unfrozen` / L6H5: Negative in all nine direct, frozen and unfrozen cells: unfrozen −0.139 zero, −0.094 mean, −0.185 resample; frozen −0.155, −0.104, −0.208; direct −0.087, −0.065, −0.134. The most negative unfrozen head effect under mean and under resample. Not selected in any set.
18. agreement / `direct_resample` / L5.mlp: Resample end of a selected cell (direct under mean −0.172, rank 9). Direct −0.150 under resample (rank 12); frozen −0.032 mean, +0.188 resample; unfrozen −0.046 mean, +0.192 resample.

#### IOI (exploratory)

| Component | Cell set | Seed 0 effect ± s | Rank | Held-out effect ± s | Verdict | Restored ± sem (Holm) |
|---|---|---|---|---|---|---|
| L9H9 | `total_mean_unfrozen` | +0.260 ± 0.013 | 19 | +0.235 ± 0.013 | replicated | 0.6907 ± 0.0071 (clears) |
| L10H0 | `total_mean_unfrozen` | +0.395 ± 0.012 | 12 | +0.383 ± 0.012 | replicated | 0.2358 ± 0.0063 (clears) |
| L8.mlp | `total_mean_unfrozen` | −0.385 ± 0.011 | 14 | −0.388 ± 0.011 | replicated | −0.0062 ± 0.0019 (clears) |
| L4H11 | `total_resample_unfrozen` | +0.4619 ± 0.0083 | 11 | +0.4479 ± 0.0080 | replicated | 0.00002 ± 0.00030 (does not clear) |
| L10H10 | `total_mean_unfrozen` | +0.1345 ± 0.0060 | 27 | +0.1223 ± 0.0061 | replicated | 0.1351 ± 0.0031 (clears) |
| L3.mlp | `total_mean_unfrozen` | −0.2201 ± 0.0097 | 20 | −0.2124 ± 0.0100 | replicated | −0.0297 ± 0.0015 (clears) |
| L3.mlp | `total_mean_frozen` | +0.1641 ± 0.0049 | 18 | +0.1587 ± 0.0049 | replicated | −0.0297 ± 0.0015 (clears) |

**L9H9** (1 cell set, replicated). Necessity: ablating L9H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.260 ± 0.013. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9H9's clean output into the corrupt run restores 0.6907 ± 0.0071 of the gap (clears Holm).

**L10H0** (1 cell set, replicated). Necessity: ablating L10H0 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.395 ± 0.012. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H0's clean output into the corrupt run restores 0.2358 ± 0.0063 of the gap (clears Holm).

**L8.mlp** (1 cell set, replicated). Necessity: ablating L8.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: −0.385 ± 0.011. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L8.mlp's clean output into the corrupt run restores −0.0062 ± 0.0019 of the gap (clears Holm).

**L4H11** (1 cell set, replicated). Necessity: ablating L4H11 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, node, unfrozen [fraction removed 0.983]: +0.4619 ± 0.0083. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L4H11's clean output into the corrupt run restores 0.00002 ± 0.00030 of the gap (does not clear Holm).

**L10H10** (1 cell set, replicated). Necessity: ablating L10H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: +0.1345 ± 0.0060. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L10H10's clean output into the corrupt run restores 0.1351 ± 0.0031 of the gap (clears Holm).

**L3.mlp** (2 cell sets, all replicated). Necessity: ablating L3.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 0.983]: −0.2201 ± 0.0097; mean, node, frozen [ref n 2,000; fraction removed 0.983]: +0.1641 ± 0.0049. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L3.mlp's clean output into the corrupt run restores −0.0297 ± 0.0015 of the gap (clears Holm).

#### Induction (exploratory)

| Component | Cell set | Seed 0 effect ± s | Rank | Held-out effect ± s | Verdict | Restored ± sem (Holm) | `shuffle_prefix` arm | END-only arm |
|---|---|---|---|---|---|---|---|---|
| L6H6 | `total_mean_unfrozen` | −1.343 ± 0.040 | 14 | −1.399 ± 0.041 | replicated | −0.00658 ± 0.00042 (clears) | −0.948 ± 0.027, same, clears | −0.370 ± 0.018, same, clears |
| L1.mlp | `total_mean_unfrozen` | −0.913 ± 0.042 | 19 | −1.052 ± 0.046 | replicated | −0.00113 ± 0.00067 (does not clear) | −0.958 ± 0.040, same, clears | −0.070 ± 0.013, same, clears |
| L1.mlp | `total_resample_unfrozen` | +0.649 ± 0.054 | 27 | +0.541 ± 0.051 | replicated | −0.00113 ± 0.00067 (does not clear) | +0.620 ± 0.049, same, clears | +0.0604 ± 0.0096, same, clears |
| L7H3 | `total_mean_unfrozen` | −1.230 ± 0.030 | 15 | −1.259 ± 0.031 | replicated | −0.00185 ± 0.00020 (clears) | −0.579 ± 0.018, same, clears | −0.851 ± 0.022, same, clears |
| L9H6 | `direct_mean` | +0.805 ± 0.016 | 11 | +0.806 ± 0.016 | replicated | 0.0777 ± 0.0013 (clears) | +0.785 ± 0.016, same, clears | = baseline, by construction |
| L6H9 | `direct_mean` | −0.477 ± 0.020 | 20 | −0.457 ± 0.019 | replicated | 0.07682 ± 0.00094 (clears) | **+0.456 ± 0.019, flipped, clears** | = baseline, by construction |
| L6H9 | `total_mean_unfrozen` | +0.804 ± 0.029 | 24 | +0.792 ± 0.030 | replicated | 0.07682 ± 0.00094 (clears) | +1.159 ± 0.029, same, clears | +0.610 ± 0.026, same, clears |
| L6H10 | `total_mean_frozen` | +1.037 ± 0.026 | 12 | +1.032 ± 0.025 | replicated | 0.00338 ± 0.00044 (clears) | +0.857 ± 0.022, same, clears | +0.560 ± 0.015, same, clears |
| L6H10 | `total_mean_unfrozen` | −0.496 ± 0.026 | 32 | −0.532 ± 0.027 | replicated | 0.00338 ± 0.00044 (clears) | **+0.582 ± 0.020, flipped, clears** | −0.528 ± 0.020, same, clears |

**L6H6** (1 cell set, replicated). Necessity: ablating L6H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: −1.343 ± 0.040. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H6's clean output into the corrupt run restores −0.00658 ± 0.00042 of the gap (clears Holm).

**L1.mlp** (2 cell sets, all replicated). Necessity: ablating L1.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: −0.913 ± 0.042; resample, node, unfrozen [fraction removed 1.000]: +0.649 ± 0.054. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L1.mlp's clean output into the corrupt run restores −0.00113 ± 0.00067 of the gap (does not clear Holm).

**L7H3** (1 cell set, replicated). Necessity: ablating L7H3 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: −1.230 ± 0.030. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L7H3's clean output into the corrupt run restores −0.00185 ± 0.00020 of the gap (clears Holm).

**L9H6** (1 cell set, replicated). Necessity: ablating L9H6 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: +0.805 ± 0.016. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L9H6's clean output into the corrupt run restores 0.0777 ± 0.0013 of the gap (clears Holm).

**L6H9** (2 cell sets, all replicated). Necessity: ablating L6H9 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: +0.804 ± 0.029; mean, edge to logits, unfrozen [ref n 2,000; fraction removed 1.000]: −0.477 ± 0.020. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H9's clean output into the corrupt run restores 0.07682 ± 0.00094 of the gap (clears Holm). Adversarial disagreement (selecting draw): under mean, edge to logits, unfrozen, the `shuffle_prefix` arm gives +0.456 ± 0.019 against the all-position `fresh_prefix` baseline −0.477 (flipped, clears Holm).

**L6H10** (2 cell sets, all replicated). Necessity: ablating L6H10 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 1.000]: −0.496 ± 0.026; mean, node, frozen [ref n 2,000; fraction removed 1.000]: +1.037 ± 0.026. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H10's clean output into the corrupt run restores 0.00338 ± 0.00044 of the gap (clears Holm). Adversarial disagreement (selecting draw): under mean, node, unfrozen, the `shuffle_prefix` arm gives +0.582 ± 0.020 against the all-position `fresh_prefix` baseline −0.496 (flipped, clears Holm).

#### Agreement (exploratory)

| Component | Cell set | Seed 0 effect ± s | Rank | Held-out effect ± s | Verdict | Restored ± sem (Holm) |
|---|---|---|---|---|---|---|
| L6H5 | `total_mean_unfrozen` | −0.0940 ± 0.0025 | 13 | −0.0951 ± 0.0024 | replicated | −0.03538 ± 0.00055 (clears) |
| L5.mlp | `direct_resample` | −0.1496 ± 0.0026 | 12 | −0.1537 ± 0.0027 | replicated | 0.0354 ± 0.0012 (clears) |

**L6H5** (1 cell set, replicated). Necessity: ablating L6H5 changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under mean, node, unfrozen [ref n 2,000; fraction removed 2.002]: −0.0940 ± 0.0025. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L6H5's clean output into the corrupt run restores −0.03538 ± 0.00055 of the gap (clears Holm).

**L5.mlp** (1 cell set, replicated). Necessity: ablating L5.mlp changes the mean logit difference by (seed 0; effect = clean − ablated, so positive lowers it and negative raises it), under resample, edge to logits, unfrozen [fraction removed 2.002]: −0.1496 ± 0.0026. Sufficiency, a separate claim: under resample restore-clean (node, all positions, unfrozen) on the held-out draw, writing L5.mlp's clean output into the corrupt run restores 0.0354 ± 0.0012 of the gap (clears Holm).

#### Set restores (exploratory)

- ioi: L4H11, L9H9, L10H0, L10H10 together restore 1.061 ± 0.011 of the gap (clears Holm); MLPs left out: L3.mlp, L8.mlp.
- induction: L6H6, L6H9, L6H10, L7H3, L9H6 together restore 0.1514 ± 0.0017 of the gap (clears Holm); MLPs left out: L1.mlp.
- agreement: L6H5 restores −0.03538 ± 0.00055 of the gap (clears Holm); MLPs left out: L5.mlp.

## 6. Null and not-replicated results

- **Not replicated: none.** 0 of 270 confirmatory and 0 of 18 exploratory
  selections failed to replicate on the held-out draw. No validation gate
  failed and the `shuffle_prefix` gate passed, so no row qualifies for the
  decision log's null table under the plan's criteria. Whether the two unmet
  expectations below get rows is the author's call.
- **Unmet expectation: the MLP rows are not blank.** §3 states, from
  [wang-2022 App. J] and [meng-2022 App. B.2], that a blank MLP row was the
  expected reading of these single-layer maps, with MLP0 the exception on
  IOI. Measured under rule A: on induction, 42 of 90 selections are MLP
  cells, 35 of them outside layer 0; on agreement, 43 of 90, 36 outside layer
  0. On IOI, 11 of 90 are MLP cells, 7 of them `L0.mlp`. The expectation
  does not hold on induction or agreement. Neither source measured those
  items, so this is a departure from the expectation as written, not a
  failed reproduction.
- **Unmet prediction: the `shuffle_prefix` corrupt mean `ld` is not ≈ 0.**
  The prediction written before the gate run was "corrupt mean ld near 0 by
  symmetry (both c and s stay in context)". Measured on
  induction/`shuffle_prefix`, n = 2,000, seed 0, BOS: −0.283 ± 0.087 (sem),
  3.3 sem below 0; in magnitude 0.016 of the gap (17.288). The gate itself
  passed; no verdict on the prediction was pre-registered.
- **Restore-clean singles that do not clear Holm** in `sufficiency_*` (some
  are a few sem from zero but do not survive the family correction; the
  necessity results for the same components stand separately). Confirmatory, 16: IOI `L1H3`, `L3H0`, `L5H5`, `L5H9`, `L8H6`;
  induction `L0H1`, `L0H3`, `L0H11`, `L1H10`, `L4H11`, `L5H9`, `L6H7`,
  `L11H0`, `L4.mlp`; agreement `L0H8`, `L5H9`. Exploratory, 2: IOI `L4H11`,
  induction `L1.mlp`. Values in the exit tables.
- **Adversarial**: 18 sign flips and 1 arm that does not clear, all in §5.
- **E2 I3's heads in the induction sets.** Under rule A,
  `L5H5` and `L2H2` are selected in no induction set. `L6H9` is selected in
  one, `direct_zero`, with a negative effect (−0.931 ± 0.024). `L4H11` is
  selected in the three unfrozen total-effect sets (ranks 4, 3, 3). Their
  ranks among the cells that clear Holm in each induction set:

| Head | `total_zero_unfrozen` | `total_mean_unfrozen` | `total_resample_unfrozen` | `total_zero_frozen` | `total_mean_frozen` | `total_resample_frozen` | `direct_zero` | `direct_mean` | `direct_resample` |
|---|---|---|---|---|---|---|---|---|---|
| `L5H5` | 15 | 31 | 33 | 70 | 69 | 66 | 39 | 53 | 53 |
| `L6H9` | 54 | 24 | 24 | 22 | 61 | 69 | 4 | 20 | 22 |
| `L4H11` | 4 | 3 | 3 | 57 | 38 | 86 | 59 | 87 | 102 |
| `L2H2` | 99 | does not clear | 51 | 67 | 44 | 83 | 81 | 64 | 84 |

  On IOI, of the three Name Movers E2 knocked out in P2 [wang-2022 App. F]
  (`results/E2/README.md` §P2), `L9H9` and `L10H0` are selected in all three frozen and all three
  direct sets and in none of the unfrozen total sets (ranks 43,
  19, 20 for `L9H9` and 22, 12, 15 for `L10H0` under zero, mean and
  resample, unfrozen); `L9H6` is selected in six frozen and direct sets with
  a positive effect and in `total_mean_unfrozen` with a negative one.
- **Same component, opposite signs across settings on one item** (rule 3:
  reported side by side, not resolved). Among the confirmatory selections:
  IOI `L0.mlp` (+5.056 under zero, node, unfrozen; −0.416 under zero, direct);
  IOI `L9H6` (−0.457 under mean, node, unfrozen; +0.977 under mean, node,
  frozen; +0.944 under mean, direct); induction `L11.mlp` (−1.752 under zero in
  the unfrozen, frozen and direct sets alike; +0.976 under mean, direct;
  +0.897 under resample, direct); agreement `L0.mlp` (+1.877 under zero, node,
  unfrozen; −0.822 under zero, direct; −0.472 under mean, direct). The
  exploratory list was built around further cases of this kind (its `why`
  lines, §5).

## 7. What this does and does not show

- **Clearing Holm is not importance.** At n = 2,000 most cells clear: 4,302 of
  the 5,616 tests in `main`. Clearing says a cell is distinguishable from no
  effect at this n, not that it is large.
- **k = 10 is ours.** The cut has no source; every exit row reports the rank
  so a reader can apply another cut. No set had a tie at the cut.
- **The five-seed sd is rough.** The reference spread for mean cells comes
  from five reference seeds; it set s (it exceeded the sem) in 30 of the
  5,616 tests in `main` and in 1 of the 270 confirmatory held-out tests.
- **The held-out draw is a fresh draw, not disjoint prompts.** It shares 3
  (IOI), 0 (induction) and 114 (agreement) of its 2,000 prompts with the
  selecting draw.
- **The normal approximation behind every z is stated, not tested.**
- **The fraction-restored sem ignores the gap's own spread**: it is the sem of
  the restore effect divided by the gap, treating the gap as fixed.
- **Necessity is not sufficiency.** The exit tables' effects are ablations
  (what changes when a component is replaced); the restore column is
  restore-clean (how much of the gap writing a clean activation in brings
  back). A component can replicate as necessary while the fraction it
  restores does not clear Holm (§6), and no sentence
  above carries a result from one direction to the other.
- **A selection is a cell, not a function.** "Selected under {settings}" is
  the claim; the sets disagree with each other by value, by freezing and
  between total and direct (§6), and those disagreements are part of the
  result.
- **The adversarial checks cover induction only**, with one second scheme
  (ours, unsourced) and END-only; 73 of the 250 arms could not have differed
  from their baseline. IOI and agreement have no second scheme in E3
  (D-016 item 8).
- **The direct effect and total − direct are recorded, not interpreted** (§3).

## 8. Observations relevant to the E4 spine decision

Measured patterns only; no decision on the spine is made or implied here.

- **Size of the frozen deltas** (median |delta| over the 143 tested deltas
  per item and value; number above 0.1 logit):

| Item | zero | mean | resample |
|---|---|---|---|
| IOI | 0.106 (75 above 0.1) | 0.020 (32) | 0.018 (30) |
| induction | 0.179 (97) | 0.065 (61) | 0.083 (64) |
| agreement | 0.020 (13) | 0.0021 (1) | 0.0015 (0) |

- **Agreement, frozen deltas outside `L0.mlp`.** Under mean, one delta of 143
  exceeds 0.1 in magnitude, `L0.mlp`'s (−0.641); the largest other in
  magnitude is `L6H0`'s (+0.025). Under resample none exceeds 0.1 (`L0.mlp`
  −0.082; largest other `L4H7`, −0.038). Under zero, 13 exceed 0.1: `L0.mlp`
  (−1.900) and 12 others, the largest `L1H10` (−0.189).
- **Largest deltas under mean on the other items.** IOI: `L9H9` +2.320, then
  `L0.mlp` −1.816. Induction: `L0.mlp` −12.449, then `L4H11` −3.554.
- **Size of the total − direct gap** (unfrozen total effect − direct effect,
  same value; median |gap| over the 156 components; number above 0.1):

| Item | zero | mean | resample |
|---|---|---|---|
| IOI | 0.097 (78 above 0.1) | 0.018 (27) | 0.014 (29) |
| induction | 0.171 (94) | 0.069 (66) | 0.083 (73) |
| agreement | 0.022 (19) | 0.0027 (6) | 0.0024 (16) |

  The largest |gap| on every item and value is `L0.mlp`'s; under mean it is
  +3.992 on IOI, +14.029 on induction and +1.549 on agreement (all three under
  mean).
- **Agreement, `L5.mlp`.** `direct_mean` selects `L5.mlp` (−0.1723 ± 0.0046,
  rank 9), and `direct_zero` (−0.189, rank 10) does too; its total-effect
  cells are smaller in magnitude under zero and mean (unfrozen −0.077 and
  −0.046, frozen −0.115 and −0.032) and positive under resample (unfrozen
  +0.192, frozen +0.188). All nine cells clear Holm.
