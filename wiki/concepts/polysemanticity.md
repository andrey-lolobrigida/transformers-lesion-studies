---
title: Polysemanticity
type: concept
status: drafted
sources: [olah-2020]
first-needed: R0
updated: 2026-08-30
---

# Polysemanticity

## In one sentence

A polysemantic neuron responds to **multiple unrelated** inputs — InceptionV1
has one that fires for cat faces, fronts of cars, and cat legs — and it is the
stated central obstacle to the circuits programme.

## Why it exists as a concept

Because the alternative is a false picture. [[feature]] makes the case that
neurons are individually understandable, and the paper immediately blocks the
over-reading: "perhaps every neuron yields a nice, human-understandable concept
if one seriously investigates it? Alas, this is not the case" [olah-2020
§Polysemantic Neurons].

Polysemanticity is what stops the circuits agenda from being a matter of
sufficient patience.

## Intuition, then mechanism

The intuition is **a word with unrelated meanings** — "bank" as riverside and
as financial institution. Nothing is shared between the senses; context
disambiguates.

**The mechanism, and where the analogy earns its keep.** The paper is careful to
rule out the obvious alternative reading. The cat/car neuron is *not* responding
to some subtle commonality between cats and cars. Feature visualization shows it
looking for the eyes and whiskers of a cat, for furry legs, and separately for
the shiny fronts of cars — three distinct things, not one abstract thing that
happens to cover all three [olah-2020 §Polysemantic Neurons].

That distinction is the entire content of the concept, and it is easy to lose.
A neuron responding to several things *is not automatically polysemantic*: the
pose-invariant dog head detector responds to left-facing and right-facing heads
and is a single coherent feature. The paper calls that **multifaceted** and
keeps it separate. Polysemantic is the subcase where the multiple latent
variables are unrelated [olah-2020 §Glossary].

**Where the analogy breaks:** with a word, context tells you which sense is
meant, and the disambiguation is external. For a neuron, the downstream circuit
has to do the disambiguating using other signals — and whether it reliably can
is not established.

## Why it is a problem, quantitatively

The paper's own framing, which is the most useful sentence on the topic:

> If one neuron with five different meanings connects to another neuron with
> five different meanings, that's effectively 25 connections that can't be
> considered individually. [olah-2020 §Polysemantic Neurons]

The damage is combinatorial, not additive. Each polysemantic node multiplies
the number of distinct interpretations an edge can carry, so the readability of
a circuit degrades much faster than the fraction of polysemantic units in it
would suggest.

The paper's verdict is blunt: polysemantic neurons are "a major challenge for
the circuits agenda, significantly limiting our ability to reason about neural
networks."

## What it licenses

Chiefly a **negative** licence, which is why the page matters here: observing
that a component activates on a set of inputs does not license naming it after
that set. The cat/car neuron would be described as a cat-face detector by
anyone who only looked at cat images.

Practically: any claim of the form "component X represents Y" needs to have
looked for the *second* thing X responds to. That is argument 2 in
[[feature-claim-evidence]] — dataset examples exist partly to check for a second
stimulus class, not just to confirm the first.

## Proposed causes and responses

- **Superposition as the cause.** The paper's hypothesis is that
  polysemanticity results from [[superposition]], where a circuit deliberately
  spreads a feature across many neurons to pack more features into a limited
  budget [olah-2020 §Polysemantic Neurons, §Circuit 3].
- **Possible resolutions, all speculative in the paper.** "Unfolding" a network
  to turn polysemantic neurons into pure features; or training networks not to
  exhibit polysemanticity in the first place. The authors connect this to the
  disentangled-representations literature while noting that literature was then
  focused on known features in generative-model latent spaces.

Read in 2026 this is the open door that sparse autoencoders walked through —
the deferred direction in D-003 and the reading list's deferred section. Zoom In
poses the problem; Elhage et al. 2022 and the monosemanticity line answer it.
Worth registering that the question is six years older than the tooling.

## Where it's contested

Not contested in this source — it is offered as an observation with a
speculative cause. The contested part is upstream: whether meaningful features
exist at all [olah-2020 §Claim 1]. A skeptic who denies meaningful features does
not need polysemanticity as an explanation of anything.

Also worth flagging as unverified from this source alone: **how common it is.**
The paper gives one vivid example and calls the problem major, but does not
report what fraction of InceptionV1's neurons are polysemantic. Any claim about
prevalence needs a different source.

## What this project does with it

- **It is the honest cost of D-003.** Choosing attention heads over SAE
  features means working with units that are not guaranteed to be pure. A head
  is, if anything, more likely to be multi-purpose than a single neuron — it is
  a larger unit. Any E3 result naming a head as doing one thing inherits this
  problem, and the decision log should not pretend otherwise.
- **It sharpens epistemic rule 1.** "Never write head X does Y" is usually
  justified on necessity/sufficiency grounds. Polysemanticity is a second,
  independent reason: even a component that genuinely does Y may also do Z, and
  the battery may not contain a task that would reveal Z.
- **It bounds what a null result means.** A head that shows no effect on all
  four battery tasks has not been shown to be unimportant. It may be doing a
  fifth thing nobody tested.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Claim 1 · Polysemantic Neurons · Circuit 3 · Glossary.

## Open questions

- What fraction of components are polysemantic, in any model? Not answered
  here. Needed before treating this as a small correction rather than a large
  one.
- Does polysemanticity at the *head* level behave like polysemanticity at the
  neuron level, or is a head with two jobs a qualitatively different thing?
  Relevant to E5 (cross-task circuit overlap), where shared components are the
  actual object of study — an overlap finding and a polysemantic head may be
  indistinguishable from ablation data alone.
