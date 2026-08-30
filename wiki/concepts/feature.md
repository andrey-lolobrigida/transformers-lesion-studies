---
title: Feature
type: concept
status: drafted
sources: [olah-2020]
first-needed: R0
updated: 2026-08-30
---

# Feature

## In one sentence

A feature is **a scalar function of the input** — in practice a direction in a
layer's activation space, often just a single neuron — that responds to an
articulable property of the input, such as "there is a curve here".

## Why it exists

Circuits need nodes. If you want to say "these components are wired together to
compute something", you first need to be able to say what each component
*represents*. Feature is the claim that such a thing exists at all: that the
units of a network are not an undifferentiated numerical soup but individually
meaningful [olah-2020 §Claim 1].

This is the paper's first and load-bearing claim, and it is deliberately stated
as a strong version of something that might turn out to be false. The authors
model this on Theodor Schwann's three claims of cell theory from 1839 — two of
which survived into modern biology and one of which was, in their words,
"horribly wrong" [olah-2020 §Three Speculative Claims]. The point of stating it
strongly is that a strong claim can be refuted.

## Intuition, then mechanism

The intuition is a **detector**. Somewhere in the network there is a unit whose
activation goes up when a curve is present and stays low otherwise. Early
layers hold simple ones — edges, curves; later layers hold elaborate ones —
floppy ears, wheels, dog heads.

**Now the mechanism, and the part the intuition hides.** The paper's actual
definition is looser and more careful than "a neuron for a thing":

> **Feature** — A scalar function of the input. In this essay, neural network
> features are directions, and often simply individual neurons.
> [olah-2020 §Glossary]

Two things follow. First, a feature is fundamentally a **direction** — a linear
combination of neurons, a vector in the layer's representation space. An
individual neuron is just the special case where that vector happens to be a
basis direction. The claim in the paper's headline is "features correspond to
directions", not "features correspond to neurons"; the neuron case is a
convenient frequent instance, not the definition.

Second, **being understandable is not the same as being obvious.** The paper is
direct that many neurons are initially mysterious and do not match anyone's a
priori guess about what features should exist. Their claim is that there is
usually a simple explanation once you find it — their example is the *high-low
frequency detector*, which looks for low-frequency texture on one side of its
receptive field and high-frequency texture on the other, apparently as a
heuristic for finding object boundaries against an out-of-focus background.
Nobody predicted it; in retrospect it is simple [olah-2020 §Example 2].

**Where the analogy breaks.** "Detector" suggests one unit, one meaning. That
is precisely what fails for a large fraction of neurons — see
[[polysemanticity]]. The paper's own vocabulary already splits this:

- **Meaningful feature** — genuinely responds to an articulable property of the
  input. May still be noisy or imperfect.
- **Pure feature** — responds to only a single latent variable.
- **Polysemantic feature** — responds to multiple *unrelated* latent variables.
- **Family** — a set of features in one layer detecting small variations of the
  same thing; curve detectors exist in a family spanning orientations, which
  jointly tile the full 360°.

Note that "meaningful" and "pure" come apart. The pose-invariant dog head
detector responds to multiple cases (left-facing and right-facing heads) and is
still a single coherent feature — the paper calls this *multifaceted* and
distinguishes it from polysemanticity, where the multiple things have nothing
to do with each other [olah-2020 §Glossary].

## What it licenses

Calling a unit "a curve detector" is a claim about what causes it to fire, and
the paper is unusually explicit that it needs evidence — seven distinct
arguments' worth. That machinery lives on its own page:
[[feature-claim-evidence]].

What a feature claim licenses, when supported: statements about *what makes the
unit activate*. What it does not license: statements about what the unit is
*for*, or that the network's behaviour depends on it. Those are separate claims
needing separate evidence — in the paper's toolkit, arguments 5–7, which are
circuit-based rather than stimulus-based.

This is the same necessity/mechanism split that epistemic rule 1 in `CLAUDE.md`
is guarding: "head X does Y" is a feature-style claim being made on
ablation-style evidence.

## Where it's contested

The paper devotes a long footnote to how genuinely divided the field is, and it
is worth not smoothing over. Some researchers treat meaningful neurons as
almost trivially real; a parallel skeptical literature argues that networks
focus primarily on texture, local structure, or imperceptible patterns; that
meaningful features, where they exist, matter less than uninterpretable ones;
and that seemingly interpretable neurons are misunderstood [olah-2020 §Claim 1].

The authors also note a *linguistic* problem underneath the empirical one:
people struggle to articulate their views because there is no clear language
for the difference between "a texture detector highly correlated with an object"
and "an object detector". That distinction is the whole disagreement, and it has
no agreed vocabulary.

Their own evidence is from thousands of hours on one vision model. They say so.

## What this project does with it

- **Mostly as background.** D-003 fixes the unit of analysis at attention
  heads, not features — features are the level the deferred SAE direction would
  work at. So this page exists to make that decision legible, not because E1–E4
  measure features.
- **The vocabulary transfers even though the substrate does not.** "Direction,
  not neuron" is exactly the framing needed for the residual stream in Elhage
  et al., and pure/polysemantic is the distinction that makes the SAE literature
  make sense if the project ever goes there.
- **The evidentiary standard transfers directly.** See
  [[feature-claim-evidence]] — that page is the reusable part of this one.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Three Speculative Claims · Claim 1 · Example 2 · Glossary.

## Open questions

- The paper's features are directions in a *convolutional channel* space. What
  the equivalent object is in a transformer's residual stream — and whether
  "feature" survives the move intact — is an Elhage/Olsson question.
