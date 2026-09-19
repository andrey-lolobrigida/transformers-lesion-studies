---
key: elhage-2021
title: A Mathematical Framework for Transformer Circuits
authors: Elhage, Nanda, Olsson, Henighan, Joseph, Mann, Askell, Bai, Chen, Conerly, DasSarma, Drain, Ganguli, Hatfield-Dodds, Hernandez, Jones, Kernion, Lovitt, Ndousse, Amodei, Brown, Clark, Kaplan, McCandlish, Olah
year: 2021
venue: Anthropic / Transformer Circuits Thread
arxiv: <not yet verified>   # no arXiv ID appears on the article page
url: https://transformer-circuits.pub/2021/framework/index.html
local: —
phase: R0
extraction: complete
feeds:
  - residual-stream
  - attention-head
  - qk-ov-circuits
  - attention-head-composition
  - induction-head
  - path-expansion
  - weight-statistics
  - pattern-preserving-ablation
  - circuit
---

# Source card — Elhage et al. 2021

Published 22 December 2021. All authors at Anthropic. First major article of
the **Transformer Circuits Thread**; Olsson et al. 2022 (`olsson-2022`) is
its direct sequel and cites it as required reading.

Authorship: Elhage, Nanda and Olsson marked core research contributors;
Henighan, Joseph and Mann core infrastructure; Olah correspondence.

**Evidence base:** zero-, one- and two-layer *attention-only* decoder
transformers trained by the authors, typically 12 heads × d_head 64
(d_model 768), with one 32-head × 128 example; context 2048, dense attention;
sinusoidal position added immediately before W_Q and W_K, so **no positional
information in the residual stream**. Training data as in Kaplan et al.
Biases dropped, LayerNorm folded. Everything about MLPs is an appendix
speculation, stated as such.

**Structural note:** the paper is a derivation followed by a reverse
engineering. The derivation (Transformer Overview) reframes the architecture;
the reverse engineering walks up the ladder zero → one → two layers, and the
two-layer section is where induction heads first appear in print. Two
post-publication additions matter: a **Summary of Follow-Up Research** (dated
February 2023) and a **Correction** to the attention-head composition diagram,
caused by a bug in the authors' low-rank library.

## Structure

| Section | What it holds |
|---|---|
| Summary of Results | The four reverse-engineering findings and seven conceptual take-aways |
| Transformer Overview | Model simplifications; residual stream as communication channel; virtual weights; bandwidth; heads independent and additive; heads as information movement; the A ⊗ W_OV form |
| Zero-Layer Transformers | W_U W_E as bigram statistics; the "direct path" |
| One-Layer Attention-Only Transformers | Path expansion; QK/OV split; freezing trick; skip-trigrams; copying; positional heads; skip-trigram "bugs"; eigenvalue copying statistic; "fully understand?" |
| Two-Layer Attention-Only Transformers | Q/K/V-composition; path expansion of logits and of attention scores; the analysed model; induction heads (function, mechanism, check); term-importance ablation; virtual attention heads |
| Where Does This Leave Us? | Transfer to large models; MLPs as 2/3 of parameters |
| Related Work | Path structure known to Dong et al.; contribution is the use, not the maths |
| Comments & Replications | Follow-up summary (Feb 2023); the composition-diagram correction |
| Additional Intuition | MLP path expansion; convolution analogy; privileged basis / bottleneck activations; pointer arithmetic with positional embeddings; identity head |
| Notation | Variable table with shapes and which activations have a privileged basis; tensor-product notation |
| Technical Details | Model details; handling LayerNorm; working with low-rank matrices |

## Extraction log

**2026-09-14 — complete.**

Read in full from the live article, including appendices, the follow-up
summary and the correction. Extracted to three new concept pages, a full
rewrite of the [[qk-ov-circuits]] stub, two new method pages, and edits to
[[induction-head]], [[pattern-preserving-ablation]] and [[circuit]]. Terms
proposed for `docs/05-glossary.md`. One open question proposed for
`docs/04-decisions.md` (O-012, which induction mechanism GPT-2 small uses).

**Deliberately left:**

- **Tensor-product notation** beyond what the pages need to state the
  A ⊗ W_OV form. The notation appendix is a reference, not a claim.
- **The convolution analogy** (§Virtual Weights and Convolution-like
  Structure). Recorded in one line on [[attention-head]]; the Cordonnier et al.
  equivalence is not this project's question.
- **The skip-trigram catalogue.** The specific Python / LaTeX / URL examples
  are illustrations of one-layer models the project will not train. The
  *shape* of the finding (copying dominates; factored form causes bugs) is on
  [[qk-ov-circuits]].
- **Working with low-rank matrices** beyond the two identities E1 will need
  (λ(AB) = λ(BA); keep matrices factored). Recorded on [[weight-statistics]].
- **Related-work and follow-up bibliographies.** R1 and R3 material.

**Recorded source inconsistencies** (flagged on the pages, not resolved):

1. The take-aways list writes the combined matrices as W_Q^T W_K and W_O W_V;
   one sentence in §Observations about Attention Heads writes "W_Q W_K" without
   the transpose before defining W_QK = W_Q^T W_K. Notational slip, not a
   different object.
2. §Analyzing a Two-Layer Model states there is "no significant V- or Q-
   composition in this particular model" and that most heads are not involved
   in any composition; the later Correction says this understated composition
   and that two induction heads also rely on a head attending to the last
   several tokens. The correction supersedes the body text.

**Not resolvable from this source, carried on the pages:** which induction
mechanism GPT-2 *small* uses (the pointer-arithmetic observation names "GPT-2"
without a size); whether the eigenvalue copying statistic is the right
formalisation (the authors say it is not settled); how important virtual
attention heads are in larger models.

## Note on citing

Section-titled and unnumbered. Wiki citations use the heading verbatim:
`[elhage-2021 §Attention Heads as Information Movement]`,
`[elhage-2021 §How Induction Heads Work]`. Appendix subsections are cited by
their own headings (`§Handling Layer Normalization`, `§Pointer Arithmetic with
Positional Embeddings`). The post-publication correction is cited as
`§Correction: Attention Head Composition Diagram`.

The paper's own BibTeX gives `journal={Transformer Circuits Thread}` with the
index.html URL, and **no arXiv ID**. The `arxiv:` field records "not checked".
