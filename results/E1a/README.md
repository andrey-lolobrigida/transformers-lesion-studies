# E1a — Ablation harness: validation on IOI

*Run 2026-09-20 on branch `phase-E1a-harness`, repo commit `db460d0`, GPT-2 small at HF
revision `607a30d7`. Interpretation of the artifacts in this directory. Decisions: D-006,
D-011, D-012; the O-011 and O-013 resolutions. Rerun: `uv run python -m src.lesion.e1a_validate`.*

## What was measured

Three checks, each a CLI run whose exact command, seed, model revision, batch size and
determinism flags are in its JSON; per-prompt values are in the parquet beside it
(zstd-compressed, which `pyarrow` reads without ceremony). The
`effect_mean` the runner reports is the mean of the per-prompt differences (clean minus
ablated), and its `sem` is the standard error of those same differences.

### 1. Identity against E0

Under **no intervention** (the harness's clean pass), on **`p_IOI`**, seed 0, 100,000
prompts, no BOS, batch size 512: mean `logit(IO) − logit(S)` at END is
3.6481308937072754 (3.648 ± 0.005), equal to `results/E0/e0_smoke_seed0_n100000.json`
bitwise on mean, std, sem, IO-over-S fraction,
mean IO probability and all 30 per-template means (`tests/test_e1a_validation.py::test_identity_against_e0`).
Artifact: `ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0.json`. The ablated half of
that artifact (zero-ablating L0H0 at all positions) is incidental and not interpreted here.

Batch size 512 is E0's and is what the bitwise comparison requires, so it is fixed rather
than tuned. At that size each forward's logits are a `[512, 20, 50257]` float32 tensor,
1.9 GB, and the first version of the runner kept three of them alive across the loop
boundary — 5.8 GB, more than this 8 GB card places. The runner now frees the clean and
ablated tensors at the end of each batch (`src/lesion/runner.py`, commit `db460d0`),
which holds the peak at two and leaves about 2 GB spare. That change frees memory only:
the numbers above were measured before it and are unchanged after it, artifact for
artifact.

### 2. Single-MLP-layer node ablation, all positions, ablate-clean, no freezing

Under **node ablation at all positions on `p_IOI`**, seed 0, n = 2,000, the mean-reference
drawn from **`p_ABC`** (n = 1,000, seed 0, matched per template; per-template counts in
each artifact), the change in mean logit difference (clean − ablated; positive = the
ablation hurt) per layer and substitution value is:

| MLP layer | zero: effect ± sem | mean (p_ABC, n=1000): effect ± sem | resample (p_ABC): effect ± sem | mean-ablated mean ld (sign) |
|---|---|---|---|---|
| 0 | +5.056 ± 0.061 | +4.052 ± 0.041 | +4.468 ± 0.047 | -0.401 (negative) |
| 1 | +0.193 ± 0.014 | -0.089 ± 0.009 | +0.147 ± 0.012 | +3.740 (positive) |
| 2 | +0.376 ± 0.015 | +0.037 ± 0.011 | +0.242 ± 0.012 | +3.615 (positive) |
| 3 | +0.191 ± 0.015 | -0.213 ± 0.010 | -0.027 ± 0.012 | +3.865 (positive) |
| 4 | +0.730 ± 0.021 | +0.309 ± 0.018 | +0.440 ± 0.020 | +3.343 (positive) |
| 5 | +0.652 ± 0.017 | +0.406 ± 0.013 | +0.531 ± 0.015 | +3.245 (positive) |
| 6 | +0.512 ± 0.017 | -0.039 ± 0.012 | +0.076 ± 0.012 | +3.690 (positive) |
| 7 | +0.066 ± 0.017 | -0.117 ± 0.011 | -0.008 ± 0.013 | +3.769 (positive) |
| 8 | -0.408 ± 0.018 | -0.386 ± 0.011 | -0.330 ± 0.013 | +4.037 (positive) |
| 9 | -0.431 ± 0.020 | +0.060 ± 0.011 | +0.056 ± 0.014 | +3.591 (positive) |
| 10 | +0.711 ± 0.016 | +0.138 ± 0.009 | +0.126 ± 0.011 | +3.514 (positive) |
| 11 | -0.307 ± 0.011 | +0.009 ± 0.007 | +0.017 ± 0.009 | +3.643 (positive) |

Clean mean logit difference on this sample: 3.651 ± 0.036. It is the same clean pass in all
36 runs — the clean forward does not depend on which component is ablated afterwards — so
one figure covers the table.

**Bracket against Wang et al. App. J.** They report that mean-ablating MLP0 alone (over
`p_ABC`) reverses the sign of the mean logit difference, and that no other single MLP layer
does much. Stated per value (D-006):

- *Mean:* under mean ablation of MLP0 the mean logit difference is -0.401, so the
  sign does reverse. No other single MLP layer moves it by more than 0.5 under this value;
  the largest elsewhere is layer 5 at +0.406 ± 0.013.
- *Zero:* under zero ablation of MLP0 the mean logit difference is -1.405, so the sign
  does reverse. Four other layers move it by more than 0.5: layer 4 (+0.730 ± 0.021),
  layer 10 (+0.711 ± 0.016), layer 5 (+0.652 ± 0.017) and layer 6 (+0.512 ± 0.017).
- *Resample:* under resample ablation of MLP0 from `p_ABC` the mean logit difference is
  -0.816, so the sign does reverse. One other layer moves it by more than 0.5: layer 5
  (+0.531 ± 0.015).

So all three values agree on the MLP0 sign reversal and disagree on how quiet the other
eleven layers are: zero ablation moves four of them past 0.5, resample one, mean none.
MLP0's effect is the largest under all three values, by a factor of at
least 6.9 over the next largest layer (zero: +5.056 against layer 4's +0.730; mean: +4.052
against layer 5's +0.406; resample: +4.468 against layer 5's +0.531).

This is a bracket, not a match (D-011): the reference size, the sample size and the word
lists are this project's, not Wang et al.'s. Where zero, mean and resample disagree, the
disagreement is the finding, not a reason to prefer one.

### 3. Determinism

Two invocations of the MLP0 command (`results/E1a/` and `results/E1a/rerun/`) produce
artifacts identical apart from `environment.seconds` and the output path, and identical
parquet tables (`test_determinism_rerun_identical`). The twin is the same command, not
merely a command with the same effect: both are the `--value all` call on `L0.mlp`, so the
recorded `cli` block and command string match too.

### Exploratory, not an exit check: the same table with pattern freezing

Same 36 runs with `--freeze` (every attention pattern pinned to its clean-run value; the
O-011 axis). First data point on MLPs for the frozen-minus-unfrozen delta before E3:

| MLP layer | zero: effect ± sem | mean (p_ABC, n=1000): effect ± sem | resample (p_ABC): effect ± sem | mean-ablated mean ld (sign) |
|---|---|---|---|---|
| 0 | +0.761 ± 0.040 | +2.189 ± 0.030 | +2.640 ± 0.043 | +1.463 (positive) |
| 1 | -0.030 ± 0.008 | +0.173 ± 0.007 | +0.208 ± 0.009 | +3.478 (positive) |
| 2 | +0.054 ± 0.008 | +0.151 ± 0.006 | +0.155 ± 0.008 | +3.501 (positive) |
| 3 | +0.085 ± 0.007 | +0.161 ± 0.005 | +0.178 ± 0.006 | +3.490 (positive) |
| 4 | +0.007 ± 0.007 | +0.113 ± 0.005 | +0.118 ± 0.006 | +3.538 (positive) |
| 5 | -0.127 ± 0.010 | +0.207 ± 0.006 | +0.220 ± 0.008 | +3.444 (positive) |
| 6 | -0.039 ± 0.010 | +0.178 ± 0.007 | +0.185 ± 0.008 | +3.474 (positive) |
| 7 | -0.429 ± 0.010 | +0.062 ± 0.008 | +0.094 ± 0.008 | +3.590 (positive) |
| 8 | -0.381 ± 0.010 | +0.036 ± 0.007 | +0.061 ± 0.008 | +3.616 (positive) |
| 9 | -0.091 ± 0.010 | +0.066 ± 0.006 | +0.070 ± 0.007 | +3.585 (positive) |
| 10 | +0.463 ± 0.012 | +0.160 ± 0.006 | +0.160 ± 0.007 | +3.492 (positive) |
| 11 | -0.307 ± 0.011 | +0.009 ± 0.007 | +0.017 ± 0.009 | +3.643 (positive) |

Counting a cell as differing when the frozen-minus-unfrozen delta exceeds three times the
larger of the two sems, 29 of the 36 (layer, value) cells differ; the seven that do not are
layer 8 under zero, layers 9 and 10 under mean, layer 9 under resample, and layer 11 under
all three values, where the two tables agree to four decimals. The largest deltas are at
layer 0: under zero ablation +5.056 ± 0.061 unfrozen against +0.761 ± 0.040 frozen, under
mean +4.052 ± 0.041 against +2.189 ± 0.030, under resample +4.468 ± 0.047 against
+2.640 ± 0.043. Under freezing the MLP0 mean-ablated mean logit difference is +1.463, so
the sign reversal in check 2 is not reproduced with patterns pinned. These are two
different interventions measured side by side; which one a given claim needs is O-011's
question and is not settled here.

## What this does and does not show

- The instrument reproduces E0's measurement exactly and is deterministic across runs.
- Ablation tests necessity only. Nothing here says what any MLP layer is *for*.
- The MLP0 result is one dataset, one corruption, one reference size. E2 varies them.
- Edge ablation and the Inputs receiver are exercised by the fast tier on a random
  two-layer model; on GPT-2 small, edge-to-logits (Wang convention) had one smoke run at
  n = 50 during harness development (written to `scratch/`, not committed) and the Inputs
  receiver had none. No edge number is interpreted in E1a.

## Files

| Stem pattern | What |
|---|---|
| `ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0` | check 1 |
| `ioi_L{0..11}mlp_{zero,mean-corrupt-n1000-s0-template,resample}_node_all_ablate-clean_n2000_seed0` | check 2 |
| `..._frozen_n2000_seed0` | exploratory frozen twin |
| `rerun/ioi_L0mlp_{zero,mean-...,resample}_n2000_seed0` | check 3 (the layer-0 call repeated; the mean artifact is the one compared) |
