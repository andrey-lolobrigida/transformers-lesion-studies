---
title: Attention head
type: concept
status: drafted
sources: [elhage-2021]
first-needed: E1
updated: 2026-09-14
---

# Attention head

## In one sentence

An attention head **moves information** from one token's residual stream to
another's, and its whole action factors into two independent pieces — an
attention pattern $A$ that says *from which token*, and a low-rank matrix
$W_{OV}$ that says *what is read and how it is written*: $h(x) = (A \otimes W_{OV}) \cdot x$.

## Why it exists

The standard presentation of attention — compute queries, keys and values,
softmax, weighted sum, concatenate all heads, multiply by one big output
matrix — is written for computational efficiency. Elhage et al. argue that the
most efficient description and the most *interpretable* description of the
same computation are usually different, and that the first job of reverse
engineering is to find the representation that makes reasoning easy
[elhage-2021 §Transformer Overview]. This page is that representation for one
head. Two facts fall out of it that the standard form hides: heads are
independent and additive, and where a head looks is separable from what it
moves.

## Intuition, then mechanism

**The analogy:** a courier. For each destination token, the courier decides
whom to collect from (the attention pattern, a set of weights over earlier
tokens), collects a parcel from each (the value), and delivers a repackaged
version to the destination's mailbox by dropping it in — adding to what is
already there. Two decisions, made by different parts of the courier's
instructions: the *route* and the *packaging*.

**Where the analogy breaks.** First, the route depends on the contents of the
mailboxes at both ends: the pattern is computed from the residual stream by a
softmax, and that softmax is the *only* non-linear step in the head. Elhage et
al. call heads "half-linear" for this reason — fix the pattern and everything
left is linear [elhage-2021 §Observations about Attention Heads]. Second, a
parcel is not delivered whole: $W_{OV}$ is rank-limited, so only a
$d_{\text{head}}$-dimensional slice of the source's stream can be read, and only a
$d_{\text{head}}$-dimensional slice of the destination's stream can be written.

**Now the mechanism.** Given the pattern, a head's output is usually written in
three steps [elhage-2021 §Attention Heads as Information Movement]:

1. value vector per token, $v_i = W_V x_i$;
2. result vector by mixing values with the pattern, $r_i = \sum_j A_{i,j} v_j$;
3. output per token, $h(x)_i = W_O r_i$.

The point of the tensor rewrite is that steps 1 and 3 multiply on the
*feature* side of $x$ (the per-token vector) while step 2 multiplies on the
*position* side. Collapsing them:

$$
h(x) = (A \otimes W_O W_V) \cdot x = (A \otimes W_{OV}) \cdot x
$$

"$A$ mixes across tokens while $W_{OV}$ acts on each vector independently."
The pattern itself is $A = \operatorname{softmax}(x^\top W_Q^\top W_K x)$, i.e. $\text{score}(i, j) = x_i^\top W_{QK}\, x_j$ with $W_{QK} = W_Q^\top W_K$, and can be computed "without
referring to keys and queries" at all [elhage-2021 §Attention Heads as
Information Movement].

**Heads are independent and additive.** The concatenate-then-multiply form is
$W_O^H [r^{h_1}; r^{h_2}; \ldots]$. Split $W_O^H$ into per-head blocks and this is
$\sum_i W_O^{h_i} r^{h_i}$ — each head multiplied by its own output matrix and
summed into the stream. The concatenated form is preferred for GPUs; the summed
form is the one to think with [elhage-2021 §Attention Heads are Independent and
Additive].

**One-line checkpoint:** a head is $A \otimes W_{OV}$; $A$ chooses the source token,
$W_{OV}$ chooses the information; they are computed by disjoint parameters and
only the softmax in $A$ is non-linear.

## Precisely

Shapes, in the paper's convention [elhage-2021 §Variable Definitions]:

| Object | Shape | Note |
|---|---|---|
| $x$ | $[n_{\text{context}}, d_{\text{model}}]$ | residual stream, one row per token |
| $W_Q, W_K, W_V$ | $[d_{\text{head}}, d_{\text{model}}]$ | read from the stream |
| $W_O$ | $[d_{\text{model}}, d_{\text{head}}]$ | write to the stream |
| $W_{QK} = W_Q^\top W_K$ | $[d_{\text{model}}, d_{\text{model}}]$ | rank $\le d_{\text{head}}$; bilinear form |
| $W_{OV} = W_O W_V$ | $[d_{\text{model}}, d_{\text{model}}]$ | rank $\le d_{\text{head}}$; linear map |
| $A$ | $[n_{\text{context}}, n_{\text{context}}]$ | softmax of scores, causally masked |
| $h(x)$ | $[n_{\text{context}}, d_{\text{model}}]$ | the head's write |

> **Convention warning for E0/E1.** TransformerLens stores per-head weights as
> `[d_model, d_head]` for Q, K, V and `[d_head, d_model]` for O, i.e. the
> transpose of the paper's shapes, so the products are written $W_Q W_K^\top$ and
> $W_V W_O$ there `[unverified — check the library's own documentation at
> E0]`. The *objects* are the same; the letters are not. Record which
> convention every harness formula uses.

**Observations the paper draws from the form** [elhage-2021 §Observations
about Attention Heads]:

- Heads move information between token positions; consequently the stream
  "will generally have linear subspaces corresponding to information copied
  from other tokens and not directly about the present token".
- $W_Q$ and $W_K$ never act separately; $W_O$ and $W_V$ never act separately.
  Keys, queries and values are "superficial" intermediates of the two low-rank
  products, and any reparameterisation of the factors that preserves the
  products gives an identical head.
- **Reading $W_{OV}$ by SVD.** With $W_{OV} = U S V$, the right singular vectors
  $V$ give the subspace of the *source* stream that is read; the left singular
  vectors $U$ give the subspace of the *destination* stream that is written.
- **Products of heads are heads.** $(A^2 \otimes W_{OV}^2)(A^1 \otimes W_{OV}^1) = (A^2 A^1) \otimes (W_{OV}^2 W_{OV}^1)$ — a *virtual attention head* with a composed pattern and a
  composed OV matrix. See [[attention-head-composition]].
- Implementing attention this way would be "horribly inefficient"; it is a
  description, not an algorithm.

**Positional heads.** In the paper's models position enters only through
$W_Q$ and $W_K$, and for sinusoidal embeddings a shift is a rotation, so $W_{QK}$
can select any relative offset. One-layer models have a small number of heads
that are "primarily positional", e.g. attending to the present or previous
token [elhage-2021 §Primarily Positional Attention Heads]. The previous-token
head that induction needs is one of these.

**The convolution reading**, recorded for E5 and left there: a sum
$\sum_h A^h \otimes W_h$ is a generalisation of a convolution in which attention heads
play the role of relative offsets; a head with a fixed relative-position pattern
*is* one convolution tap [elhage-2021 §Virtual Weights and Convolution-like
Structure].

## What it licenses

The decomposition is an **identity**, not a finding: for any head, on any
input, $h(x) = (A \otimes W_{OV})\, x$ holds exactly (up to LayerNorm handling, see
[[residual-stream]]). What it licenses is separating two questions that
ordinary language runs together:

| Question | Object | How it is answered |
|---|---|---|
| Where does this head look? | $A$, via $W_{QK}$ | inspect the pattern; or the QK circuit's weights |
| What does it move if it looks there? | $W_{OV}$ | inspect the OV circuit's weights; or the direct-path logit effect |

It does **not** license saying what a head "does". A head with a copying
$W_{OV}$ and a previous-token $A$ does one thing; the same $W_{OV}$ with an
induction-style $A$ does another. Behaviour is the pair, on a distribution.

## Where it's contested

- Nothing in the derivation is contested; the paper says the maths is "for the
  most part not novel" and credits Dong et al. for the path structure
  [elhage-2021 §Related Work: Mathematical Framework].
- **The independence is exact only with patterns fixed.** Since $A$ depends on
  $x$, and $x$ at layer 2 contains layer-1 heads' writes, "where a head looks"
  can depend on "what another head moved". That is composition, and it is the
  whole subject of [[attention-head-composition]].
- **Biases and LayerNorm are dropped.** Biases can be folded (and in
  attention-only models mostly become logit biases); LayerNorm's per-token
  scalar cannot be, and is carried as a path reweighting [elhage-2021 §Model
  Simplifications, §Handling Layer Normalization].

## What this project does with it

- **The E1 harness's unit is $h(x)$, the write.** Ablating a head means
  replacing its write to the stream (zero, mean, resample per D-006).
  Recording *direct effect* means $W_U h(x)$ alone. Pattern-preserving
  ablation means freezing $A$ and zeroing the write. All three are operations
  on objects named on this page; see [[path-expansion]] and
  [[pattern-preserving-ablation]] for the licences.
- **E2's induction reproduction** needs a previous-token head (a positional
  $A$) and a copying $W_{OV}$ in a later head; the check is on
  [[weight-statistics]].
- **D-003's unit of analysis is this object.** A head has 4 matrices, or
  equivalently 2 low-rank ones; that is small enough to inspect and is what
  the published numbers are about.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Transformer Overview · Model Simplifications · Attention
  Heads are Independent and Additive · Attention Heads as Information Movement ·
  Observations about Attention Heads · Primarily Positional Attention Heads ·
  Virtual Weights and Convolution-like Structure · Related Work · Variable
  Definitions · Handling Layer Normalization.

## Open questions

- With MLPs present, does the "write" the harness ablates still decompose
  cleanly into the head's direct and indirect routes, or does the MLP's
  non-linearity make "the head's contribution to later value computations"
  ill-defined? Olsson et al. name two failure modes (see
  [[pattern-preserving-ablation]]); nothing here adds to them. R1.
