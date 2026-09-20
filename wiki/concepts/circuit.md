---
title: Circuit
type: concept
status: drafted
sources: [olah-2020, elhage-2021, wang-2022, miller-2024]
first-needed: R0
updated: 2026-09-19
---

# Circuit

## In one sentence

A circuit is a **subgraph of a neural network** — a small set of tightly linked
features together with the weights connecting them — chosen to be small enough
that you can read a meaningful algorithm off those weights.

## Why it exists

Most interpretability work before this tried to explain the behaviour of a
whole network. That turns out to be very hard to do in a way that is *checkably
true*: networks are complicated enough that it is difficult even to formalise
what an interesting empirical claim about one would be. The result, Olah et al.
argue, is that the field ended up evaluating whether an interpretability
*method* seemed useful rather than whether it produced true statements
[olah-2020 §Interpretability as a Natural Science].

The circuits move is to shrink the object of study until claims about it become
falsifiable. A claim about a whole network is hard to refute. A claim about
eleven weights between two neurons is not: if you understand the circuit, you
should be able to predict what changes when you edit those weights. For small
enough circuits, the paper notes, statements about their behaviour become
questions of mathematical reasoning [olah-2020 §Interpretability as a Natural
Science].

The cost is stated plainly and is worth keeping: statements about circuits are
**much smaller in scope** than statements about model behaviour. The bet is
that model behaviour can eventually be decomposed into circuit-level statements
— not that it already has been.

## Intuition, then mechanism

The paper's own analogy is **anatomy**, or more precisely cellular biology. A
microscope let biology stop treating an organism as a unit and start treating
cells as the object of inquiry — not a gain in precision but a change in what
kind of question could be asked. Circuits are proposed as the same move for
neural networks: not "the network classifies dogs" but "these four neurons,
wired this way, detect a dog head facing left."

**Now the mechanism.** In the vision network the paper studies (InceptionV1, a
convolutional image classifier from 2014), every neuron is a linear combination
of the previous layer's neurons followed by a ReLU (rectified linear unit — the
function that passes positive values through and clamps negative ones to zero).
So if you understand what the neurons in both layers represent, the weights
between them are directly readable. A positive weight means the earlier neuron
*excites* the later one; a negative weight means it *inhibits* it [olah-2020
§Claim 2].

The worked example: a curve detector in a later layer connects to an earlier,
cruder curve detector through a 5×5 grid of weights. Those weights are strongly
positive **arranged in the shape of a curve** — meaning that at each point along
the curve it expects, the detector is looking for a tangent curve in the earlier
layer. Curves in the opposite orientation are inhibitory at every point
[olah-2020 §Circuit 1].

**Where the analogy breaks, and it matters here.** Anatomy suggests parts with
fixed locations and dedicated wiring. Two problems for this project:

1. **The paper's circuits are convolutional.** An edge is a literal weight
   matrix between two neurons in adjacent layers. A transformer has a *residual
   stream* — a shared bus that every component reads from and writes to — so
   "the weight between two nodes" is not a single object you can look up. Every
   component is in some sense connected to every later one. The transformer
   version of this concept comes from Elhage et al. 2021, not from here — and
   it does supply the missing object: the **virtual weight** between two
   components is the product of the earlier one's write matrix and the later
   one's read matrix through the stream, `W_in² W_out¹` [elhage-2021 §Virtual
   Weights]. An edge in a transformer circuit is a virtual weight; the
   composition scores on [[weight-statistics]] are its normalised size. See
   [[residual-stream]].
2. **Structural versus behavioural circuits.** Zoom In's circuits are read off
   *weights*. This project will identify candidate circuits by *ablation* — by
   breaking things and watching behaviour. Those are not the same object and
   the confusion between them is worth guarding against; see "What it licenses"
   below.

## Precisely

From the paper's own glossary [olah-2020 §Glossary]:

> **Circuit** — A subgraph of a neural network. Nodes correspond to neurons or
> directions (linear combinations of neurons). Two nodes have an edge between
> them if they are in adjacent layers. The edges have weights which are the
> weights between those neurons (or `n₁ W n₂ᵀ` if the nodes are linear
> combinations). For convolutional layers, the weights are 2D matrices
> representing the weights for different relative positions of the layers.

Note what this definition does *not* contain: any reference to a task, a
behaviour, or a dataset. It is purely structural.

**The behavioural definition, from Wang et al. 2022** — added 2026-09-19.
Think of the model as a computational graph `M` "where nodes are terms in
its forward pass (neurons, attention heads, embeddings, etc.) and edges are
the interactions between those terms"; then "a circuit `C` is a subgraph of
`M` responsible for some behavior (such as completing the IOI task)". The
authors say directly that this "is more coarse-grained than the one
presented in Olah et al. (2020), where nodes are features … instead of model
components" [wang-2022 §2.1]. Two things follow that Zoom In's definition
does not have:

- **A circuit has a function.** `C(x)` is defined as the logits of `M` on
  `x` with every node outside `C` *knocked out* — so the knockout method
  (in the paper, [[mean-ablation]] on `p_ABC`) is part of what the circuit
  *is*, not a way of testing it afterwards [wang-2022 §2.1].
- **Nodes are (component, position) pairs.** The 26-head circuit is "1.1%
  of the total number of (head, token position) pairs" [wang-2022 §1].

The two definitions coexist in the paper's own practice: the circuit is
*found* by [[path-patching]] (causal, behavioural), *characterised* by
attention patterns and OV-matrix copy scores (structural), and *validated*
by knockouts ([[circuit-validation-criteria]]).

Related vocabulary the paper defines alongside it:

- **Direction** — a linear combination of neurons in a layer; equivalently a
  vector in that layer's representation space. An individual neuron is the
  special case of a basis direction. Circuit nodes are directions, not
  necessarily neurons.
- **Client neuron / client feature** — a later-layer neuron that relies on a
  particular earlier one. A circle detector is a client of curve detectors.
- **Upstream / downstream** — in an earlier layer / in a later layer.

## What it licenses

A structural circuit claim of the Zoom In kind licenses a **mechanistic**
statement: this is how the computation is assembled, and here is the prediction
that follows. Its strongest form of evidence is weight editing — the paper
proposes reimplementing curve detection by hand-setting weights and checking it
mimics the original [olah-2020 §Claim 1, Argument 7].

It does **not** license a necessity claim on its own. Reading an algorithm off
the weights does not establish that the network's behaviour depends on that
pathway in practice — there may be other pathways doing the same job.

The reverse also holds and is the one that will bite this project: **an
ablation result does not by itself give you a circuit in this sense.** Ablation
establishes that behaviour degrades without a component. It says nothing about
what the component computes or how it is wired to its neighbours. A heatmap of
ablation effects is a map of *where damage matters*, not a circuit diagram.
See `docs/00-motivation.md` on phrenology risk.

## Where it's contested

- **The community is divided on the premise.** The paper is explicit that
  meaningful features are not an agreed fact — a skeptical literature argues
  networks rely primarily on texture or on imperceptible patterns, and that
  seemingly interpretable neurons are misunderstood [olah-2020 §Claim 1]. The
  circuits programme presupposes the thing that is disputed.
- **Polysemanticity is a stated limitation, not a footnote.** The paper calls
  polysemantic neurons "a major challenge for the circuits agenda, significantly
  limiting our ability to reason about neural networks" — if one neuron carrying
  five meanings connects to another carrying five, that is effectively 25
  connections that cannot be considered individually [olah-2020 §Polysemantic
  Neurons]. See [[polysemanticity]].
- **This project's own working definition now has a source.**
  `docs/05-glossary.md` defines a circuit behaviourally — "a subgraph of
  components that together implement a behaviour" — and adds that which
  subgraph counts depends partly on the ablation methodology. That is Wang
  et al.'s definition, and the caveat is a direct consequence of it: `C(x)`
  is *defined* through a knockout, so a different knockout defines a
  different `C(x)` [wang-2022 §2.1]. Miller et al. (R1) make the
  consequence empirical. **Proposed reconciliation for D-010 item 3:** keep
  both senses, named — a *structural* circuit (Zoom In; Elhage et al.'s
  virtual weights) is read off parameters; a *behavioural* circuit (Wang et
  al.) is a component subgraph plus the knockout that defines its function.
  Results docs say which one a claim is about. **Accepted by the author
  2026-09-20 (D-010 closure).**
  *Strengthened by Miller et al. (2026-09-19):* even the behavioural sense
  is underdetermined by the task alone. In a compiled Tracr model with a
  known program, the ground-truth circuit *differs* between zero and
  resample ablation — an edge that carries only input-invariant positional
  information is required under one and not the other — so "the optimal
  circuit with respect to only a set of prompts is undefined. The ablation
  partly determines the task" [miller-2024 §5]. A behavioural circuit is a
  component subgraph *plus* the full ablation six-tuple on
  [[ablation-methodology]], not plus "the knockout" in the abstract.

## What this project does with it

- **R0 exit criterion** requires writing what a circuit is, cold and without
  looking. This page is what that note gets checked against afterwards — not
  the source for writing it.
- **E3 produces heatmaps, not circuits.** Ablating every head and scoring the
  battery yields a functional map. Calling the result a circuit would be exactly
  the necessity/mechanism confusion described above.
- **D-003** fixes the unit of analysis at attention heads rather than features,
  which means this project mostly works one level coarser than Zoom In does.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Virtual Weights.

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 1 · 2.1 · 3.3.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 1 · 5 · 6.

- [olah-2020] Olah, Cammarata, Schubert, Goh, Petrov & Carter, "Zoom In: An
  Introduction to Circuits", Distill, 10 March 2020.
  DOI 10.23915/distill.00024.001 ·
  https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Claim 1 · Claim 2 · Circuit 1 · Polysemantic Neurons ·
  Interpretability as a Natural Science · Glossary.

## Open questions

- **How does a weight-read circuit relate to an ablation-identified one?**
  Zoom In defines circuits structurally; this project finds candidates
  behaviourally. *Partly answered at the Wang extraction (2026-09-19):* Wang
  et al. use both on the same object — path patching to find nodes, OV copy
  scores and attention patterns to say what they do — and list the purely
  structural checks (QK collision detection, OV copying of positional
  embeddings, Elhage-style parameter analysis) as validations they *omitted*
  [wang-2022 §3.3]. So the two did not converge in the source; one was done
  and the other deferred. What to call the object is the reconciliation
  proposed above. Remains a candidate `O-00N` only if the author wants it
  tracked beyond D-010.
- ~~Does the residual stream make "subgraph" the wrong shape entirely, or just
  a harder one to compute?~~ Resolved at the Elhage extraction (2026-09-14):
  harder to compute, not the wrong shape. Nodes are heads (and MLPs), edges are
  virtual weights, and the graph is dense by construction — every later
  component has a virtual weight to every earlier one — so a "circuit" is the
  sparse subgraph of edges that are large and used. Elhage et al. add a
  complication Zoom In did not have: an edge can be of three kinds (Q, K or V
  composition) with different meanings, see [[attention-head-composition]].
