# E0 — Environment and smoke test

*Run 2026-09-20 on branch `phase-E0-environment`. Interpretation of the
artifacts in this directory. Decision: D-011; open question: O-014.*

## What was measured

Under **no ablation**, on **`p_IOI`** built from Wang et al.'s released
templates and word lists (`src/lesion/ioi.py`), GPT-2 small (HF revision
`607a30d7`) gives the following mean `logit(IO) − logit(S)` at the position
before the answer:

| Seed | Tokenisation | Templates | n | Mean logit diff ± sem | IO over S | Mean IO prob |
|---|---|---|---|---|---|---|
| 0 | no BOS | 15 per order | 100,000 | 3.648 ± 0.005 | 99.41% | 52.7% |
| 0 | no BOS | 7 per order (derived) | — | 3.485 | — | — |
| 0 | BOS | 15 per order | 100,000 | 3.922 ± 0.006 | 98.93% | 52.0% |
| 1 | no BOS | 15 per order | 100,000 | 3.650 ± 0.005 | 99.41% | 52.8% |
| 1 | BOS | 15 per order | 100,000 | 3.924 ± 0.006 | — | — |
| — | *published* [wang-2022 §2] | *15, "mixed"* | *100,000* | *3.56* | *99.3%* | *49%* |

"7 per order (derived)" is the mean of the per-template means for templates
0–6 of each order, which is what the released code's `mixed` mode samples
when given its default template count. It is computed from the same run, not
sampled separately.

## What this does and does not show

- The environment works end to end: CUDA on sm_120, TransformerLens load at a
  pinned revision, a hook that fires and can modify an activation, bitwise
  determinism across two passes over the same batch, and a 100,000-prompt
  measurement in about 70 s. Steps 1–4 of the smoke test are hard failures;
  all pass.
- The published 3.56 is **not matched at two decimals**. It is bracketed by
  the two no-BOS readings of the template mix (3.49 and 3.65). The BOS
  tokenisation misses by 0.36, about seventy standard errors, and is excluded
  as the paper's procedure on that evidence alone.
- The secondary statistics land close: IO chosen over S 99.4% vs 99.3%; mean
  IO probability 52.7% vs 49%.
- The residual gap cannot be closed from the sources: the released lists have
  99 names, 8 places and 8 objects where the paper says 100, 20 and 20, and
  the code history begins after the paper's v1. The per-template means span
  2.5 to 5.0, so the template mix alone moves the baseline by more than the
  gap. This is a design-choice uncertainty on every absolute IOI level in
  Wang et al., not a defect of the model or the environment.
- Nothing here licenses any claim about any head. It is a clean baseline.

## Rerun

```
uv sync
uv run python -m src.lesion.e0_smoke --n 100000 --seed 0
uv run python -m src.lesion.e0_smoke --n 100000 --seed 1
uv run pytest
```

Each artifact records the command, seed, repo commit, model revision, package
versions, GPU, determinism flags and per-template means.

## Files

| File | What |
|---|---|
| `e0_smoke_seed0_n100000.json` | The run in the table, seed 0 |
| `e0_smoke_seed1_n100000.json` | Same, seed 1 |
