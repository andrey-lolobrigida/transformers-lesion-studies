---
title: Residual stream
type: concept
status: drafted
sources: [elhage-2021]
first-needed: E1
updated: 2026-09-14
---

# Residual stream

## In one sentence

The residual stream is the per-token vector that every layer reads from with a
linear map and writes to by **adding** a linear map of its result — a shared,
purely linear communication channel that does no computation of its own.

## Why it exists

The term exists to replace "embedding". Elhage et al. prefer "residual stream"
for two reasons: it emphasises that the vector is a running *sum* of everything
written so far, and it fights the intuition that the vector is *about the
present token* — in practice, subspaces of it hold information copied in from
other tokens [elhage-2021 §Virtual Weights and the Residual Stream as a
Communication Channel].

The concept earns a page because "component X reads what component Y wrote" is
the basic relation every circuit on this project is made of, and it is only
well-defined once you have the stream: without it, "the weight between two
heads" is not an object you can point at. See [[circuit]] for where the Zoom In
notion of a subgraph strains against this.

## Intuition, then mechanism

**The analogy:** a whiteboard in a shared office. Each worker (a head, an MLP)
walks up, reads whatever part of the board they care about, does their work at
their desk, and comes back to *add* a note. Nobody erases. By the end, the board
is the original note plus every addition, and a worker late in the day can read
a note left by one early in the day even though they never met.

**Where the analogy breaks.** A whiteboard has regions with names — "top left
corner". The residual stream does not: it has **no privileged basis**. You could
rotate the whole space, rotate every matrix that touches it, and the model would
behave identically [elhage-2021 §Virtual Weights and the Residual Stream as a
Communication Channel]. So "dimension 37 of the stream" means nothing on its
own; only *subspaces defined by what reads and writes them* mean anything. And
the board is small: there are far more things wanting to write than there is
room, which is the paper's "bandwidth" argument below.

**Now the mechanism.** Every attention layer and every MLP layer reads its input
from the stream by a linear projection and writes its output back by adding
another linear projection. The stream is "simply the sum of the output of all
the previous layers and the original embedding" [elhage-2021 §High-Level
Architecture, §Virtual Weights…]. That additive, linear structure is unusual —
even ResNets put a non-linearity on their residual path — and it is what
licenses the three consequences the paper draws:

1. **Virtual weights.** Any two layers, however far apart, are implicitly
   connected by the product of the earlier one's output weights and the later
   one's input weights, e.g. $W_I^2 W_O^1$, describing how much the later layer
   reads of what the earlier one wrote [elhage-2021 §Virtual Weights].
2. **Subspaces as memory.** Once written, information persists in its subspace
   until something actively deletes it. The stream is hundreds to tens of
   thousands of dimensions; a head touches a 64- or 128-dimensional slice and
   can easily write somewhere no other head reads [elhage-2021 §Subspaces and
   Residual Stream Bandwidth].
3. **Bandwidth is scarce.** A single MLP layer has four times more neurons than
   the stream has dimensions; at layer 25 of a 50-layer model the stream is
   mediating between roughly 100× more neurons before it and 100× more after
   it, "somehow communicating in superposition". The paper calls such tensors
   **bottleneck activations** and expects them to be unusually hard to
   interpret directly [elhage-2021 §Subspaces and Residual Stream Bandwidth,
   §Activation Properties].

From (3) the authors speculate that some components do **memory management**:
MLP neurons with strongly negative cosine similarity between input and output
weights, and heads with large negative $W_{OV}$ eigenvalues that mostly attend to
the present token, may be deleting information others wrote. Stated as "hints",
not a result [elhage-2021 §Subspaces and Residual Stream Bandwidth].

**One-line checkpoint:** the stream is an additive bus with no named wires;
components are connected by what they read and write, and that connection is a
matrix product you can compute.

## Precisely

With $t$ the one-hot tokens $[n_{\text{context}}, n_{\text{vocab}}]$, $W_E$ the embedding
$[d_{\text{model}}, n_{\text{vocab}}]$ and $W_U$ the unembedding $[n_{\text{vocab}}, d_{\text{model}}]$
[elhage-2021 §Variable Definitions]:

- $x^0 = W_E t$ (plus positional embedding, in architectures that add one to
  the stream — the paper's own models do not; see below).
- Each residual block: $x^{n+1} = x^n + \sum_h h(x^n) + m(x^n + \sum_h h(x^n))$,
  attention heads then MLP, each adding.
- Logits $T(t) = W_U x^{\text{final}}$.

**Which activations have a privileged basis.** Tokens, attention patterns and
MLP activations do. The residual stream, keys, queries and values do **not**.
"It doesn't really make sense to look at the 'neurons' (ie. basis dimensions)
of activations like the residual stream" [elhage-2021 §Activation Properties].

**Handling LayerNorm.** Every read from the stream passes through LayerNorm.
Subtracting the mean is a fixed linear map (it zeroes one direction); the
learned diagonal scale and bias are affine; both fold into the adjacent weights.
What is left is division by the standard deviation — a *scalar* per token that
commutes with everything else on a path — so the authors treat it as "a
variable reweighting of the set of path terms going through that layer
normalization". Cost: paths through different layers stop being directly
comparable [elhage-2021 §Handling Layer Normalization].

**The paper's models put no position in the stream.** Sinusoidal position is
added just before $W_Q$ and $W_K$, so position affects attention scores but is
never written to the residual stream. GPT-2 does add a positional embedding to
the stream, which "opens up" mechanisms unavailable to the paper's models —
notably pointer arithmetic on positions [elhage-2021 §Model Details, §Pointer
Arithmetic with Positional Embeddings]. See [[induction-head]] and O-012.

## What it licenses

The stream is an architectural fact, not a hypothesis, so nothing needs to be
"demonstrated" about its existence. What the concept licenses is a *vocabulary
of claims*:

- "Head 2 reads a subspace head 1 writes" is demonstrated, at the weight level,
  by a non-trivial virtual weight $W_{\text{in}}^2 W_{\text{out}}^1$ — the composition scores on
  [[weight-statistics]] are exactly this, normalised.
- That is a statement about **parameters**. Whether the model *uses* that
  connection on a given input is a separate, behavioural question, answered by
  intervention (ablation for necessity, patching for sufficiency — epistemic
  rules 1–2). A large virtual weight with no behavioural consequence is
  possible and, per the paper, common: "most attention heads have a much
  smaller composition than random matrices" [elhage-2021 §Analyzing a
  Two-Layer Model].

## Where it's contested

- **Memory management is a speculation.** The paper offers it as "hints" and
  immediately notes the same mechanisms could be *conditional* deletion. No
  result in the paper depends on it.
- **LayerNorm folding is an approximation with a named remainder.** The
  per-token scalar is not folded; it is carried as a reweighting. Any claim
  that treats the stream as exactly linear has to say what it did with that
  scalar. This is the same scalar that E4 calls mechanical self-repair.
- **The paper's stream carries no position; GPT-2's does.** Every mechanism
  claim in the paper is made for models where heads cannot read position from
  the stream. Transfer to GPT-2 small is asserted in general terms
  [elhage-2021 §Where Does This Leave Us?] but not for any specific head.

## What this project does with it

- **E1 hooks live here.** Total-effect ablation replaces a head's *write* to
  the stream; direct effect reads only the write's contribution through $W_U$
  (the direct path, see [[path-expansion]]). Both are operations on the stream,
  and the harness should name them that way.
- **E4's decomposition is this paper's LayerNorm scalar.** D-002's "mechanical
  component" of self-repair is the variable per-token rescaling that Elhage et
  al. fold out of the path expansion [elhage-2021 §Handling Layer
  Normalization]. That gives E4 a precise statement of what is being controlled
  for, and a 2021 provenance for the idea alongside Olsson's §Argument 3 caveat
  already noted under O-011.
- **O-007 (MLPs as first-class components).** The bandwidth argument is the
  reason MLPs cannot be ignored even in an attention-focused harness: they are
  the largest writers to the stream.
- **D-003 (heads, not features).** The no-privileged-basis fact is the formal
  reason a residual-stream *dimension* is not a unit of analysis, and why the
  feature-level direction needs a learned basis (SAEs) — the tooling burden
  D-003 declined.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: High-Level Architecture · Virtual Weights and the Residual
  Stream as a Communication Channel · Virtual Weights · Subspaces and Residual
  Stream Bandwidth · Analyzing a Two-Layer Model · Where Does This Leave Us? ·
  Activation Properties · Pointer Arithmetic with Positional Embeddings ·
  Variable Definitions · Model Details · Handling Layer Normalization.

## Open questions

- Does GPT-2 small's positional embedding in the stream change which
  induction mechanism its heads use? Proposed as O-012.
- How much of the stream's dimensionality does the E3 sweep actually
  perturb per ablation? Nothing here says; a cheap diagnostic at E1 would be
  the norm of each head's write relative to the stream norm at that layer.
