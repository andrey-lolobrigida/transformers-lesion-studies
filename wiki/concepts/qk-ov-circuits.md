---
title: QK and OV circuits
type: concept
status: stub
sources: [olsson-2022]
first-needed: R0
updated: 2026-09-08
---

# QK and OV circuits

> **Stub, deliberately thin.** Everything here comes from Olsson et al.'s
> summary section, which is itself a set of pointers back to Elhage et al. 2021,
> "A Mathematical Framework for Transformer Circuits" — not yet read, not yet
> extracted. The page exists so that [[induction-head]] and
> [[head-activation-evaluators]] have somewhere to point, and so the gap is
> visible rather than silent. **Do not implement anything from this page.**

## In one sentence

A single attention head splits into two largely independent computations: the
**QK circuit** decides *where* the head attends, and the **OV circuit** decides
*what it writes* to the residual stream if it attends there.

## Why it exists

Because the split is real rather than notational, and it is what makes several
of this paper's methods possible at all:

- The two are "separable... implemented by different circuits consisting of
  different sets of parameters which may be run and studied in isolation"
  [olsson-2022 §Data Collection (2)]. This is the structural fact that licenses
  [[pattern-preserving-ablation]] — you can freeze one and intervene on the
  other.
- The two induction-head evaluators partition along the same line: copying is an
  OV property, prefix matching and previous-token attention are QK properties
  [olsson-2022 §Data Collection (3)].

## What Olsson et al. state, and nothing more

- **The QK circuit** is written `C_QK^h`, the transformation applied to one-hot
  token vectors to produce the attention pattern:
  `A^h = softmax*(tᵀ · C_QK^h · t)`. It expands into many terms, one per path
  through the model that maps tokens to attention scores; deeper models have
  more terms [olsson-2022 §Data Collection (4)].
- **K-composition** means a head's `W_K` reads from a subspace written by an
  earlier attention head. The basic induction head uses pure K-composition with
  a previous-token head, producing a term `Id ⊗ h_prev ⊗ W` where `W` has
  positive eigenvalues [olsson-2022 §Summary of Reverse Engineering Induction
  Heads].
- **Q-composition** is the same idea on the query side, and is what GPT-2's
  alternative positional mechanism reportedly uses.
- **Positive eigenvalues** of an OV matrix characterise copying; positive
  eigenvalues of the QK `W` indicate "same-matching" — preferring query and key
  components to agree [olsson-2022 §Data Collection (4)].
- For the attention pattern, the identity of the attended token is "quite
  irrelevant"; for the output it is essential [olsson-2022 §Summary of Reverse
  Engineering Induction Heads].

## What it licenses

Nothing, yet — and that is the point of recording it. Everything above is
reported at second hand by a paper that summarises it in a section explicitly
labelled as unfollowable without reading the original. Citing the eigenvalue
tests or the composition vocabulary on the strength of this page would be
citing a summary of a summary.

What the split *will* license, once read properly, is the separation the method
pages already lean on: an intervention on where a head looks is a different
experiment from an intervention on what it writes, and the two are separable in
the parameters rather than only in the telling.

## What is missing and must come from Elhage et al.

Everything that would let this page be used: the derivation of the split, what
`W_QK` and `W_OV` are as matrices, why the eigenvalue tests mean what they are
said to mean, what the residual stream is such that "reads from a subspace
written by an earlier head" is well defined, and the path-expansion machinery
the QK term above is one term of.

**R0's exit criterion requires writing what the QK and OV circuits of a head do,
cold and without looking.** This page cannot support that and is not meant to —
it is a placeholder marking that the concept exists and has not yet been
understood from its source.

## Sources

- [olsson-2022] Olsson et al., "In-context Learning and Induction Heads",
  Transformer Circuits Thread, 8 March 2022.
  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
  Sections cited: Summary of Reverse Engineering Induction Heads · Data
  Collection (2) · Data Collection (3) · Data Collection (4).
- Elhage et al. 2021 — **not yet read.** Source card not yet created.

## Open questions

- Everything above. Reopen this page during the Elhage extraction and expect to
  rewrite it rather than extend it.
