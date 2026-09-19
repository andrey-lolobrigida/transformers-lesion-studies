---
key: olsson-2022
title: In-context Learning and Induction Heads
authors: Olsson, Elhage, Nanda, Joseph, DasSarma, Henighan, Mann, Askell, Bai, Chen, Conerly, Drain, Ganguli, Hatfield-Dodds, Hernandez, Johnston, Jones, Kernion, Lovitt, Ndousse, Amodei, Brown, Clark, Kaplan, McCandlish, Olah
year: 2022
venue: Anthropic / Transformer Circuits Thread
arxiv: <not yet verified>   # no arXiv ID appears on the article page or in its own citation block
url: https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
local: papers/olsson-2022-induction-heads/in-context-learning-and-induction-heads/index.html
phase: R0
extraction: complete
feeds:
  - induction-head
  - in-context-learning
  - phase-change
  - qk-ov-circuits
  - pattern-preserving-ablation
  - head-activation-evaluators
---

# Source card — Olsson et al. 2022

Published 8 March 2022. All authors at Anthropic. Second major article of the
**Transformer Circuits Thread**; builds directly on Elhage et al. 2021 and is
not fully readable without it — §Summary of Reverse Engineering Induction Heads
says so explicitly.

Authorship: Olsson, Elhage and Nanda marked core research contributors; Joseph,
DasSarma, Henighan and Mann core infrastructure; Olah correspondence.

**Evidence base:** 34 decoder-only transformers in four families — small
attention-only (1–6L), small with MLPs (1–6L), full-scale with MLPs (4L/13M
through 40L/13B), and "smeared key" architectural variants (1–2L). One training
run each. 200 snapshots per small model, 14–15 per full-scale model. Over 50,000
individual attention-head ablations, small models only. Per-token losses on a
fixed set of 10,000 examples × 512 tokens.

**Structural note:** the paper is organised as six numbered arguments, each
opening with a table grading its own evidence across model classes
(Strong/Medium/Weak × Causal/Correlational/Mechanistic/Interventional/Analogy).
The overall thesis — induction heads are the mechanism for the *majority* of
in-context learning — is graded Strong+Causal only for small attention-only
models and Medium+Correlational for large ones, by the authors themselves.

## Structure

| Section | What it holds |
|---|---|
| Key Concepts | The two conceptions of in-context learning; the ICL score; the behavioural definition of an induction head; per-token loss PCA |
| Argument 1 (co-occurrence) | The phase change: ICL, induction heads, loss bump and PCA pivot moving together; the confounds |
| Argument 2 (co-perturbation) | Smeared-key architecture; ICL appears in 1-layer models when induction becomes expressible |
| Argument 3 (ablation) | The strongest evidence; also the LayerNorm/redundancy masking caveat |
| Argument 4 (generality) | Three heads in the 40L model doing copying, translation, pattern matching while still scoring as induction heads |
| Argument 5 (mechanism) | QK/OV summary, K-composition, the separate GPT-2 pointer-arithmetic mechanism |
| Argument 6 (continuity) | Extrapolation from small to large; the "other composition mechanisms" alternative |
| Model Analysis Table / Model Details | Architectures, training, snapshot schedules, hyperparameter changes |
| Unexplained Curiosities | Constant ICL score; loss-derivative inversion; four anomalous heads/models |
| Discussion | Safety implications; no evidence of mesa-optimisers |
| Comments & Replications | Scherlis (Redwood) and Lieberum (independent), invited |
| Appendix | Where induction heads form; score distributions; evaluator validation; data collection; analyses |

## Extraction log

**2026-09-08 — complete.**

Read in full from the live article (`index.html`), including appendix and the
two invited replications. Extracted to three concept pages, one stub and two
method pages (see `feeds`). Sixteen terms proposed for `docs/05-glossary.md`.
One open question proposed for `docs/04-decisions.md` (attention-pattern
freezing as a third ablation axis).

**Deliberately left:**

- **Per-token loss PCA as a technique.** Described in §Per-Token Loss Analysis
  and used for the trajectory figures. Recorded on [[phase-change]] as far as it
  bears on O-010's visualisation question, but no method page: it is a
  presentation device in this paper, not a measurement anything is concluded
  from, and opening a page would overstate its role.
- **The smeared-key architecture** beyond the formula and result on
  [[phase-change]]. It is an architectural intervention on models trained for
  the purpose; nothing in E0–E6 trains a model.
- **Scaling-laws and learning-dynamics related work.** Belongs to R3 if
  anywhere.
- **The Harry Potter per-token anecdote.** Explicitly labelled anecdata by the
  authors and used for qualitative intuition only.

**Recorded source inconsistencies** (flagged on the pages, not resolved):

1. Phase-change window given as "roughly 2.5 to 5 billion tokens" in §Argument 1
   and "approximately 1 – 3 billion tokens in the small models" in §Model
   Details.
2. The pattern-matching head is layer 8 in the §Argument 4 table and layer 26 in
   the §Behavior 3 prose.
3. "Up to 12B parameter models" in §Argument 4 versus 13B non-embedding
   parameters for the 40-layer model in the model properties table.
4. The in-context learning score is defined as loss(500) − loss(50), which is
   negative under in-context learning, but is reported as positive nats
   throughout.

**Post-publication corrections.** The change log records 2022-09-20: the
definition of prefix matching was corrected in two places, having incorrectly
said "tokens that were *preceded* by the current token" rather than "followed
by"; and the copying evaluator's ReLU step was added to the description. A
secondary source quoting the pre-correction wording is quoting an erratum. A
2023-03-06 entry is typo fixes only.

**Not resolvable from this source, carried on the pages:** which induction
mechanism GPT-2 small uses; what threshold makes a head an induction head;
whether full and pattern-preserving ablation disagree numerically; the sign
convention of the plotted in-context learning score.

## Note on citing

The article is section-titled and unnumbered, like the Distill articles. Wiki
citations use the section heading verbatim: `[olsson-2022 §Argument 3]`,
`[olsson-2022 §Data Collection (3)]`. Appendix subsections are cited by their
own headings (`§Where induction heads form`).

The paper's own BibTeX gives `journal={Transformer Circuits Thread}` with the
index.html URL as a note, and **no arXiv ID**. The `arxiv:` field above records
"not checked", not "does not exist" — `CLAUDE.md` forbids supplying one from
memory.
