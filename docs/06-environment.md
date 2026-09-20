# 06 — Environment

Verified during E0 (2026-09-20). Sections marked *verified* were checked by
running `uv run python -m src.lesion.e0_smoke`; the rest is still anticipation.
Correct in place as reality intervenes, and record anything that cost more
than an hour in the gotcha log.

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
with. *Verified:* with `CUBLAS_WORKSPACE_CONFIG=:4096:8` set before CUDA
initialises and `torch.use_deterministic_algorithms(True)`, two forward
passes over the same batch are bitwise identical, and the 100,000-prompt
means agree across separate process invocations. The smoke test checks this
on every run.

**Model revisions.** Pin the HuggingFace revision hash for every model, not
just the name. Record it in every results artifact.

## Install (verified 2026-09-20)

The project is a `uv` project; `pyproject.toml` and `uv.lock` are the record.
`uv sync` recreates the environment; `uv run ...` runs inside it.

| Component | Verified value |
|---|---|
| Driver / CUDA runtime on the host | 595.84 / CUDA 13.2 |
| Python | 3.12.12 (uv-managed) |
| torch | 2.14.0+cu130, the default PyPI wheel; arch list includes `sm_120` |
| transformer-lens | 3.9.0 |
| transformers | 5.17.0 |
| GPT-2 small | HF `openai-community/gpt2` at revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`, pinned in `src/lesion/e0_smoke.py` |

Nothing had to be pinned or downgraded: `uv add transformer-lens` resolved
a torch build with Blackwell kernels on its own, and the sm_120 matmul check
passed on the first try. The anticipated CUDA fight did not happen.

The full E0 run (100,000 prompts × 2 tokenisations, GPT-2 small, batch 512)
takes about 70 s per tokenisation on the 5060 and peaks well under 8 GB.

Original install order, kept for reference: (1) confirm driver and CUDA,
(2) fresh venv, (3) torch with a real CUDA op checked, (4) TransformerLens,
(5) `auto-circuit` when E1 needs it, (6) nothing speculative.

## Deferred

- **nnsight / NDIF** — only if TransformerLens becomes a ceiling. Its
  `remote=True` mode runs interventions on large hosted models with the same
  code, which is the escape hatch if a question genuinely needs scale.
- **SAELens** — deferred with the SAE direction (D-003).

## Gotcha log

*Anything that cost more than an hour goes here, with the fix.*

| Date | Problem | Fix |
|---|---|---|
| 2026-09-20 | **TransformerLens prepends BOS silently.** `HookedTransformer.from_pretrained` mutates the tokenizer it is given (or loads) so that every call adds `<\|endoftext\|>` in front, and `model(str)` does the same. The paper's released code feeds tokens without BOS. On p_IOI the difference is large: 3.65 vs 3.92 mean logit difference. | Tokenise with a *separate* plain `AutoTokenizer` and `add_special_tokens=False`, add BOS explicitly when wanted, and assert the first id is not BOS. Report both tokenisations side by side; never let a default choose. |
| 2026-09-20 | **The released IOI templates include the answer.** `"... gave a [OBJECT] to [A]"` — the IO name is the last word of the stored text, and the released code reads logits at the position *before* it (its `end` index). Reading the last position gives a meaningless number (mean logit diff ≈ 1.5, IO probability ≈ 0). | `IOIPrompt.prompt` strips the trailing answer; `encode()` asserts `tokens(prompt) + [IO] == tokens(text)` so the alignment the paper relies on is checked, not assumed. |
| 2026-09-20 | The paper's word lists are not what the released code contains: 99 names (paper: 100), 8 places and 8 objects (paper: 20 each). The repository history starts after the paper's v1, so the paper-era lists are unrecoverable. | Use the released lists verbatim, pin their sizes in `tests/test_ioi.py`, and treat the published 3.56 as a bracket, not a target for exact match (D-011). |
| 2026-09-20 | `transformer_lens` has no `__version__` attribute in 3.9.0. | `importlib.metadata.version("transformer-lens")`. |
| 2026-09-20 | One transient `CUDACachingAllocator ... OOM` warning during model load while another process held VRAM; the run recovered and results were unaffected. | None needed; noted so it is not mistaken for a real failure later. Check `nvidia-smi` if it recurs. |
