---
key: miller-2024
title: Transformer Circuit Faithfulness Metrics Are Not Robust
authors: Miller, Chughtai, Saunders
year: 2024
venue: arXiv preprint (v1, 11 July 2024); FAR AI / independent. Acknowledgments thank "anonymous reviewers at COLM 2024"; acceptance [unverified from this copy]
arxiv: 2407.08734   # verified: printed on the arXiv HTML page header, "arXiv:2407.08734v1 [cs.LG] 11 Jul 2024"
url: https://arxiv.org/abs/2407.08734
local: papers/miller-2024-faithfulness/2407.08734.html
phase: R1
extraction: complete
feeds:
  - ablation-methodology
  - resample-ablation
  - circuit-validation-criteria
  - mean-ablation
  - zero-ablation
  - activation-patching
  - path-patching
  - pattern-preserving-ablation
  - logit-difference
  - circuit
  - ioi-circuit
---

# Source card — Miller, Chughtai & Saunders 2024

Read from the arXiv v1 HTML rendering (local copy). Three authors; Miller
at FAR AI, the other two independent. Releases the `AutoCircuit` library
(edge patching; mean, zero, resample; TransformerLens models; benchmarked
against the official ACDC implementation).

**Evidence base:** re-evaluation of three published circuits under varied
ablation methodology — IOI (GPT-2 small, Wang et al.), Docstring (4-layer
attention-only model, Heimersheim & Janiak), Sports Players (Pythia 2.8B,
Nanda et al.) — plus two compiled Tracr models (Reverse, X-Proportion) with
known ground-truth programs, used to test three automated circuit-discovery
algorithms (ACDC, Subnetwork Probing, Head Importance Scoring). No new
circuits; no ablation of single components for their own sake. Mean
ablations over 100 ABC prompts for IOI. Most results are figures; few
numbers appear in the text.

**Structural note:** Section 3 is a taxonomy (the six-tuple, Tables 1–3);
Section 4 is the IOI case study (sensitivity to each axis, then per-prompt
variance); Section 5 is the Tracr argument that the optimal circuit is
undefined without an ablation methodology; Section 6 states the thesis and
two recommendations. Appendix F maps the paper's vocabulary onto Redwood's
(path patching = edge resample ablation; causal scrubbing = branch resample
ablation on the treeified model).

## Structure

| Section | What it holds |
|---|---|
| 1 Introduction | The question: what do faithfulness metrics show? |
| 2 Related Work | Zhang & Nanda 2024 as the nearest prior; faithfulness as a continuum |
| 3.1 Ablation Methodology | eq. 1; the six axes; Table 1 (the tuple); Table 2 (seven prior works) |
| 3.1.1–3.1.5 | Granularity; node/edge/branch and the three model views; value (zero, noise, resample, mean); token positions; direction × set (Table 3, Fig. 2) |
| 3.2 Metric | A free seventh choice |
| 4 | IOI: logit difference recovered; Wang et al.'s methodology restated, incl. ≈ 7 examples per template |
| 4.1 | Sensitivity: edge vs node; resample vs mean; positions; BABA vs ABBA; mean set size; averaging order |
| 4.2 | Per-prompt variance; IQR up to 50 points; extreme outliers |
| 5 | Tracr X-Proportion: ground truth differs by ablation value; perfect recovery when matched |
| 6 | "The task cannot be separated from the ablation methodology"; recommendations |
| App. A | AutoCircuit |
| App. B | The residual, factorised and treeified views; per-position edges |
| App. C | Task table with example prompts and metrics |
| App. D | Docstring and Sports Players re-evaluations; Tracr circuits |
| App. E | Edge- vs node-based discovery |
| App. F | Nomenclature crosswalk to Redwood's papers |

## Extraction log

**2026-09-19 — complete.**

Read in full from the local HTML copy. Opened [[ablation-methodology]] (the
six-tuple; the paper's frame, now the frame for every ablation page here)
and [[resample-ablation]]. Edited [[circuit-validation-criteria]] (the IOI
sensitivity results; per-prompt variance; the Tracr argument),
[[mean-ablation]] (Wang et al.'s reference size, per this source; monotone
set-size effect), [[zero-ablation]] (stub → drafted: what question zero
ablation asks), [[activation-patching]] (direction × set table; nomenclature),
[[path-patching]] (= edge resample ablation; MLPs in the direct path),
[[pattern-preserving-ablation]] (pattern freezing absent from the taxonomy),
[[logit-difference]] (logit difference recovered; averaging order),
[[circuit]] (Tracr: ground truth depends on ablation value) and
[[ioi-circuit]] (re-evaluation summary). Terms proposed for
`docs/05-glossary.md`. Addenda proposed to O-003, O-007, O-011 (the R1
trigger), O-013.

**Deliberately left:**

- **Automated circuit discovery** (ACDC, SP, HISP, ROC curves, Appendix E).
  Not this project's method; recorded only as the vehicle for the Tracr
  argument.
- **AutoCircuit's performance benchmark** (App. A, Fig. 6). An E0 question.
- **Docstring and Sports Players details** beyond the one result each
  contributes to [[resample-ablation]].
- **Gaussian-noise ablation.** Named as a value; ROME (R1 skim) is its
  source.
- **Causal scrubbing and branch ablation** beyond the definition. Chan et
  al. is the R1 skim.

**Recorded source inconsistencies / gaps** (flagged on the pages):

1. Nearly all sensitivity results are given as figures; the text quotes
   Wang et al.'s 87% and the Sports Players 0% / 33% and no other
   faithfulness values. Pages say "read off figures" where that is so.
2. The monotone effect of mean-ablation set size is reported without a
   mechanism. `docs/01-methods.md` attributes a mechanism ("noisy means
   push the model toward specific wrong answers") to this paper that does
   not appear in the v1 text — flagged for the D-010 review.
3. Wang et al. are cited as 2023 (ICLR) throughout; this wiki's key is
   `wang-2022` after the arXiv v1 date.

**Not resolvable from this source, carried on the pages:** whether the
six-tuple sensitivity transfers to single-component effect sizes; where
attention-pattern freezing sits in the taxonomy; the IOI numbers behind the
figures; what set size stabilises a mean on GPT-2 small.

## Note on citing

Numbered sections and lettered appendices. Wiki citations:
`[miller-2024 §3.1.5]`, `[miller-2024 App. F]`, tables and figures by
number, the ablation equation as `eq. 1`. The arXiv ID is verified from the
page header; the venue is not stated in the v1 text.
