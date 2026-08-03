# 06 — Environment

Filled in properly during E0. Everything below is anticipated rather than
verified; correct it in place as reality intervenes, and record anything that
cost more than an hour.

## Hardware

RTX 5060, 8 GB VRAM. Blackwell architecture, compute capability **sm_120**.

VRAM budget for planned work:

| Workload | Approximate VRAM |
|---|---|
| GPT-2 small (124M) forward | ~1 GB |
| Pythia-410M forward | ~2 GB |
| Full-model ablation sweeps (batched) | Well under 8 GB |
| Training TinyStories from scratch (E6 only) | Fits; hours, not days |

The card is not the constraint on anything through E4.

## Anticipated gotchas

**Blackwell / CUDA version.** sm_120 needs a recent CUDA toolkit — check the
installed PyTorch build actually supports it before installing anything else. A
library that pins an older torch can silently drag in a build without sm_120
kernels, which fails at first CUDA call rather than at install time. Verify
with a trivial `torch.cuda` matmul before touching TransformerLens.

**TransformerLens dependency pins.** It reimplements models rather than
wrapping HuggingFace, which is what makes hooking clean but also means its
torch pin matters more than usual. If it conflicts with the working torch
build, prefer fixing the environment over downgrading torch.

**Determinism.** Ablation results should be exactly reproducible. Set seeds,
disable nondeterministic kernels where possible, and record the flags. If a
number moves between runs, that's a bug to find in E0, not a mystery to live
with.

**Model revisions.** Pin the HuggingFace revision hash for every model, not
just the name. Record it in every results artifact.

## Install order (draft — verify in E0)

1. Confirm GPU driver and CUDA toolkit version.
2. Fresh virtual environment.
3. PyTorch build matching CUDA version; verify sm_120 with a real CUDA op.
4. TransformerLens.
5. `auto-circuit` (Miller et al.) — likely useful in E1.
6. Everything else as needed. No speculative installs.

## Deferred

- **nnsight / NDIF** — only if TransformerLens becomes a ceiling. Its
  `remote=True` mode runs interventions on large hosted models with the same
  code, which is the escape hatch if a question genuinely needs scale.
- **SAELens** — deferred with the SAE direction (D-003).

## Gotcha log

*Anything that cost more than an hour goes here, with the fix.*

| Date | Problem | Fix |
|---|---|---|
| — | — | — |
