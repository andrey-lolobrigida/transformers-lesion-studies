---
title: Superposition
type: concept
status: stub
sources: [olah-2020]
first-needed: R0
updated: 2026-08-30
---

# Superposition

> **Stub.** Everything here comes from Zoom In, where superposition is named and
> illustrated with one circuit but not analysed. The real treatment is Elhage
> et al. 2022, "Toy Models of Superposition" — which is in the **deferred**
> section of the reading list (D-003), so this page is expected to stay thin.

## In one sentence

Superposition is a network **spreading a feature across many neurons that are
mostly doing something else**, so that it can represent more features than it
has neurons.

## Why it exists

To explain [[polysemanticity]]. Having established that some neurons respond to
unrelated things, the paper needs an account of why — and the answer it reaches
is that polysemanticity is not an accident of messy training but something the
network appears to do on purpose [olah-2020 §Circuit 3].

## Intuition, then mechanism

The observation that produces the concept is specific and worth keeping,
because it is stronger evidence than a general argument would be.

In `mixed4c`, a mid-to-late layer of InceptionV1, there is a car-detecting
neuron built the way you would hope: it looks for wheels at the bottom of its
window and windows at the top. Then, instead of building a purer car detector in
the next layer, the model **spreads the car feature across a number of neurons
that are primarily dog detectors** [olah-2020 §Circuit 3].

That ordering is what makes the example load-bearing. One could imagine a world
where detecting cars and dogs were somehow entangled, making polysemantic
neurons unavoidable. What is actually seen is a model that *had* a pure neuron
and then deliberately mixed it into others. The paper's word for this is
superposition.

**Why a network would do this.** To conserve neurons for more important tasks.
As long as cars and dogs do not co-occur, the model can accurately recover the
dog feature at a later layer, so it stores the car feature without dedicating a
neuron to it. The underlying fact is geometric: a space of dimension $n$ admits
only $n$ orthogonal vectors, but exponentially many **almost** orthogonal ones
[olah-2020 §Circuit 3].

**Where the intuition breaks.** "Spreading" suggests loss or dilution. The claim
is the opposite — the feature is recoverable, which is exactly why the trade is
worth making. The cost is not fidelity but interpretability: recovery requires
reading a direction rather than a neuron, and only the network knows which
direction.

## What it licenses

A structural claim about *representation*, not about behaviour. Nothing here is
measured by ablation, and the evidence offered is one circuit in one model.

The practical licence is again negative and matters for this project: **a
feature's absence from a neuron is not the feature's absence.** If a capability
is stored in superposition, ablating any single unit that carries part of it
will show a small effect, and the natural but wrong reading is that no unit
matters.

## Where it's contested

Not argued in this source — it is proposed on the strength of one circuit, and
the paper presents it as an interpretation ("we believe", "presumably"). Treat
the mechanism as a hypothesis with a vivid instance, not an established result,
until a source that actually tests it is read.

## What this project does with it

- **Directly relevant to reading E3 heatmaps.** A capability held in
  superposition across many heads produces a heatmap with no bright spots. That
  pattern has at least two readings — the capability is distributed, or nothing
  in the battery tests it — and superposition is the reason the distributed
  reading is live. This belongs in the caveats that ship with the figure
  (`docs/00-motivation.md`, phrenology risk).
- **It is the pressure behind the SAE direction** that D-003 defers. Sparse
  autoencoders exist because of this problem. Knowing that keeps the deferral
  honest: the project is choosing a unit of analysis known to be leaky, for
  reasons of tractability and published-number availability.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Polysemantic Neurons · Circuit 3.

## Open questions

- Does superposition happen at the level of **attention heads**, or only within
  MLP neuron spaces? The Zoom In example is a convolutional channel phenomenon.
  If heads superpose, D-003's unit of analysis is leakier than assumed. Not
  answerable from this source; keep open through R0 and R1.
