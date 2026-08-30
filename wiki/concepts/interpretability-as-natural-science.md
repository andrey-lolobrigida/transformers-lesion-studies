---
title: Interpretability as a natural science
type: concept
status: drafted
sources: [olah-2020]
first-needed: R1
updated: 2026-08-30
---

# Interpretability as a natural science

## In one sentence

The proposal that interpretability work should be evaluated the way natural
science is — by whether its empirical claims about a specific network are
**falsifiable and true** — rather than by benchmark scores or user studies.

## Why it exists

Because the field had no agreed way to tell good work from bad. The paper
reaches for Thomas Kuhn's *The Structure of Scientific Revolutions*, and the
distinction it borrows is worth stating properly: Kuhn separates **normal
science**, where a community has a paradigm, from **extraordinary science**,
where it lacks one — either because it never had one or because crisis broke it.
Extraordinary science is not the glamorous state the name suggests. It is a
period in which researchers struggle to be productive [olah-2020
§Interpretability as a Natural Science].

The authors' claim is that interpretability in 2020 was pre-paradigmatic: no
consensus on what the objects of study are, what methods answer questions about
them, or how to evaluate results. They quote Ian Goodfellow: "For
interpretability, I don't think we even have the right definitions."

## Intuition, then mechanism

Two responses to that vacuum were already on offer, each borrowed from an
adjacent field. Researchers from a deep-learning background wanted an
**interpretability benchmark** that scores how effective a method is.
Researchers from human-computer interaction wanted **user studies**.

The paper proposes a third: treat the network as an object of empirical
investigation, like an organism, and make claims about it that could be held to
the standard of **falsifiability**.

**The mechanism — why this was not already happening.** The authors' diagnosis
is the interesting part. It is very difficult to make robustly true statements
about a whole network's behaviour, and hard even to formalise what the
interesting empirical statements would be. So evaluation drifted toward whether
a *method* seems useful rather than whether we are learning true things — not
from carelessness, but because the true-statement route looked closed.

Circuits reopen it by shrinking the target. A tiny subgraph admits rigorous
empirical investigation; a circuit claim is falsifiable because understanding a
circuit should let you predict what changes when you edit its weights. For
small enough circuits, statements about behaviour become questions of
mathematical reasoning.

**Where the framing breaks down.** The stated cost: circuit-level statements are
much smaller in scope than statements about model behaviour. The bet — and the
paper is clear it is a bet — is that behavioural statements could eventually be
*decomposed* into circuit statements, making circuits "a kind of epistemic
foundation for interpretability". That decomposition has not been demonstrated.

There is also a tension the paper does not resolve. The natural-science framing
is used both to *justify* qualitative work (the Closing Thoughts argue the
discovery of cells was a qualitative result and changed the world anyway) and to
*demand* falsifiability. Those pull in different directions, and which one is
operative depends on which claim is under pressure.

## What it licenses

This is a framing, not a method — it licenses nothing on its own. What it
supplies is a **standard**: an interpretability claim should name what
observation would falsify it.

That standard is directly checkable and mostly absent from practice, which
makes it the most portable thing in the paper.

## Where it's contested

Not defended against objections in this source; it is offered as a proposal. Two
that go unaddressed:

- **Falsifiable about *which* network?** A prediction confirmed on InceptionV1
  is a statement about InceptionV1. Its reach depends entirely on
  [[universality]], which the same paper concedes is anecdotally supported at
  best. The natural-science framing and the honest universality section sit
  slightly awkwardly together.
- **Benchmarks did not go away.** The reading list's Mueller et al. 2025 (MIB,
  a standardised circuit-localisation evaluation) is the benchmark path
  continuing. Whether it and this framing are rivals or complements is a live
  question, deferred with O-002.

## What this project does with it

This is the intellectual ancestor of `CLAUDE.md`'s epistemic rules, and reading
it that way is useful — the rules are a specific implementation of a general
standard proposed here.

- **Rule 1** ("never write head X does Y", write the measurement instead) is
  falsifiability applied to phrasing: the rewritten form names the conditions
  under which it could fail.
- **Rule 6** (every number needs a rerun command, a seed, and a model revision
  hash) is what falsifiability costs in practice. A claim nobody can re-run is
  not falsifiable in any useful sense.
- **Rule 7** (a clean result triggers an adversarial check, not a writeup) is
  the same standard turned on your own findings.
- **R1's exit criterion** — writing `docs/01-methods.md` in your own words,
  stating what each measurement licenses — is this framing made specific to this
  project. Worth rereading this section before writing that document.

The honest caution: this project's primary output is E3's heatmaps, and a
heatmap is a *descriptive* artifact. It does not come with a falsifiable
prediction attached. The natural-science standard says one should be added —
which is what the roadmap already requires when it says any head singled out as
important gets verified by activation patching before it is named.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Interpretability as a Natural Science · Closing Thoughts.
  Kuhn attribution: the authors credit conversations with Tom McGrath at
  DeepMind for the connection — the same McGrath as the Hydra Effect paper in
  R2.

## Open questions

- What is the falsifiable prediction attached to an E3 heatmap? If none can be
  written, that says something about what the phase produces, and it is better
  known before the figures are made than after. Resolve in R1.
