---
title: Weight-based head statistics
type: method
status: drafted
sources: [elhage-2021]
first-needed: E2
updated: 2026-09-14
---

# Weight-based head statistics

Two summary numbers computed from a head's weights alone, no forward pass: the
**eigenvalue copying score** and the **composition scores**.

## In one sentence

Eigenvalue positivity of an OV (or composed QK) circuit is evidence that the
matrix maps tokens toward themselves — copying, or same-matching — and a
normalised Frobenius norm of a virtual weight is evidence that one head reads
what another writes; both are data-free and neither is a behavioural claim.

## Claim-licence block

| | |
|---|---|
| **Answers** | "Is this matrix, on average, mapping a token's direction to itself?" (eigenvalues). "Does head h₂'s Q/K/V read overlap head h₁'s write more than chance?" (composition). Both are statements about **parameters**. |
| **Does NOT answer** | Whether the head *does* copy on any input (that is Olsson's copying evaluator, a forward-pass measurement). Necessity or sufficiency of anything. Whether the composition is *used*. "Not all matrices with positive eigenvalues are things we necessarily want to consider to be copying" [elhage-2021 §Detecting Copying Behavior]. |
| **Confounds** | Non-orthogonal eigenvectors can make an all-positive-eigenvalue matrix decrease some tokens' own logits. Copying may be of an attribute (gender, number, tense), not a token. Composition scores need a random-matrix baseline subtracted and the paper's own were once computed wrong. Convention: whether `W_E`/`W_U` are multiplied in changes the object. LayerNorm folding. |
| **Always log** | Exactly which matrix (`W_OV` vs `W_U W_OV W_E`; which composed term); the baseline subtraction procedure; the weight convention used; model revision hash. |

## Why it exists

The expanded OV and QK tables have billions of entries; "searching for the
largest entries is interesting" but does not scale, and the authors ask for a
summary statistic. Copying is "fundamentally about mapping the same vector to
itself", which "seems unusually amenable to being captured in some kind of
summary statistic" [elhage-2021 §Summarizing OV/QK Matrices, §Detecting
Copying Behavior]. Composition scores answer the analogous need one level up:
which pairs of heads, out of all pairs, are worth looking at.

## Intuition, then mechanism

**Copying.** If attending to token `A` should raise the logit of `A`, the OV
circuit should send the direction "A" back toward "A". An eigenvector with a
positive real eigenvalue is exactly a direction sent to a positive multiple of
itself — "a linear combination of tokens which increases the linear
combination of logits of those same tokens". A random matrix of this kind has
eigenvalues symmetric around zero (Ginibre-like); a copying one is skewed
positive [elhage-2021 §Detecting Copying Behavior].

**Where it breaks.** Eigenvectors need not be orthogonal, so the eigenvalue
picture and the "each token raises its own logit" picture can disagree on
individual tokens; positive eigenvalues mean copying "on average". And
eigenvectors generally have mixed signs, so the picture is really two sets of
tokens each raising their own set and lowering the other — e.g. singular vs
plural [elhage-2021 §Detecting Copying Behavior].

**Composition.** A virtual weight `W_in^{h₂} W_out^{h₁}` is large when the
subspaces overlap. Normalising by the two norms and subtracting what random
matrices of the same shape give leaves a number that is near zero for most
pairs and positive for the few that matter.

## Precisely

**Eigenvalue copying statistic** [elhage-2021 §Detecting Copying Behavior]. For
`M = W_U W_OV^h W_E` (or the composed QK matrix `W` of a term), compute the
eigenvalues and summarise their positivity; the paper plots them and reports a
per-head number, then a histogram over heads. Result in the 12-head one-layer
model: "10 out of 12 heads are significantly copying", agreeing with manual
inspection. Alternatives the paper names, all consistent with each other via
trace = Σ diagonal = Σ eigenvalues: the diagonal's sign; how often a random
token's own logit is the most (or top-k most) increased.

For induction heads, plot each head at (QK-matrix positivity, OV-matrix
positivity); the induction heads sit "in an extreme right hand corner"
[elhage-2021 §Checking the Mechanistic Theory]. The authors pre-empt a
circularity objection: heads were selected for *large* K-composition, and
nothing about that implies *positive* eigenvalues — the positivity is the
independent evidence.

**Composition scores** [elhage-2021 §Analyzing a Two-Layer Model]:

    Q:  ‖W_QK^{h₂ T} W_OV^{h₁}‖_F / (‖W_QK^{h₂ T}‖_F · ‖W_OV^{h₁}‖_F)
    K:  ‖W_QK^{h₂}   W_OV^{h₁}‖_F / (‖W_QK^{h₂}‖_F   · ‖W_OV^{h₁}‖_F)
    V:  ‖W_OV^{h₂}   W_OV^{h₁}‖_F / (‖W_OV^{h₂}‖_F   · ‖W_OV^{h₁}‖_F)

minus "the empirical expected amount for random matrices of the same shapes".

**The bug, recorded because E2 will reimplement this.** The authors' low-rank
library applied a transpose identity valid for traces and eigenvalues
(`Tr(AB) = Tr(BA)`, `λ(AB) = λ(BA)`) to the Frobenius norm, where it is not
valid. Instead of `‖W_Q^{h₂T} W_K^{h₂} W_O^{h₁} W_V^{h₁}‖_F` they computed a
cyclic rotation such as `‖W_K^{h₂} W_O^{h₁} W_V^{h₁} W_Q^{h₂T}‖_F`. The quantity
they accidentally computed measures whether the induction head's query is built
from the subspace the previous-token head moved data into, which is exactly
what an induction head's K-composition should look like — so the bug
highlighted induction composition and hid other kinds. Only one figure was
affected; corrected figure shows more composition [elhage-2021 §Correction:
Attention Head Composition Diagram].

**Computing with low-rank matrices** [elhage-2021 §Working with Low-Rank
Matrices]. Keep everything factored at the narrowest point (`d_head`).
Eigenvalues: `λ(AB) = λ(BA)`, so a `50k × 50k` product's eigenvalues come from
a `64 × 64` one. SVD of a product: SVD each factor, SVD the small core
`S_A V_A U_B S_B`, recombine.

## What it licenses

- Positive OV eigenvalues license: *this head's OV circuit, multiplied through
  the embeddings, is copying on average.* Evidence, "improbable by default",
  "empirically aligned with copying" — and, per the authors, "not a dispositive
  proof that a matrix is copying in all senses one might reasonably mean"
  [elhage-2021 §Detecting Copying Behavior].
- A high K-composition score licenses: *the key side of h₂ reads a subspace
  h₁ writes, more than chance.* It does not license "h₁ feeds h₂ during
  induction"; that needs the behavioural test on [[induction-head]] and then an
  intervention.
- Neither is an ablation result. Under epistemic rule 1, a sentence built on
  these alone reads "under the eigenvalue statistic on W_U W_OV W_E, head X has
  positivity Y" — and stops.

## Where it's contested

- **The formalisation is open**, by the authors' own account: "we don't yet
  feel like we have a clear right answer" on summarising OV/QK matrices; the
  eigenvalue statistic is "quite strong evidence" and "not perfect".
- **The published composition figure was wrong.** See above.
- **Baseline subtraction is under-specified.** "Empirical expected amount for
  random matrices of the same shapes" — distribution unstated.

## What this project does with it

- **E2 pre-screen.** Compute OV eigenvalue positivity for all 144 heads of
  GPT-2 small, and Q/K/V-composition scores for every (earlier, later) head
  pair; plot the QK-vs-OV positivity scatter. This is cheap, runs before any
  ablation, and gives E2 a candidate list that the behavioural evaluators
  ([[head-activation-evaluators]]) and then ablation/patching test. Record
  the convention and the baseline.
- **O-010 candidate 3** is the K-composition score over Pythia checkpoints.
- **Implementation note.** `[unverified]` TransformerLens exposes factored
  QK/OV objects; if so, use them rather than materialising `n_vocab × n_vocab`
  matrices. Confirm at E0.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Summarizing OV/QK Matrices · Detecting Copying Behavior ·
  Analyzing a Two-Layer Model · Checking the Mechanistic Theory · Correction:
  Attention Head Composition Diagram · Working with Low-Rank Matrices.

## Open questions

- Which positivity summary does E2 use — fraction of positive real parts,
  sum, or trace-normalised? The paper plots but does not define a scalar.
  Choose one, write it down, and check that it ranks the paper's example heads
  the same way if their weights are ever available.
