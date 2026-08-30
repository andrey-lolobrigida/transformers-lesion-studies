---
title: Circuit motif
type: concept
status: drafted
sources: [olah-2020]
first-needed: E5
updated: 2026-08-30
---

# Circuit motif

## In one sentence

A recurring abstract pattern found across many different circuits — borrowed
from systems biology, where a motif is a wiring pattern that shows up repeatedly
in transcription networks and biological neural networks.

## Why it exists

Because understanding one motif gives you leverage on every graph where it
occurs, rather than on one graph [olah-2020 §Circuit Motifs]. It is the move
from cataloguing instances to naming the pattern.

The authors go further than "useful": they think studying motifs may in the long
run be **more important than the study of individual circuits** — while adding
the caveat that motif investigation is best served by first building a solid
foundation of well-understood individual circuits. Pattern-finding before you
have instances is how you find patterns that are not there.

## The three the paper names

Each is introduced through a specific circuit earlier in the article rather than
asserted abstractly.

**Equivariance.** The symmetry of the problem shows up as a symmetry in the
weights. Curve detectors exist in a family spanning orientations, and the weights
connecting an early curve detector to a later one **rotate with the orientation
of the detector** [olah-2020 §Circuit 1]. Same algorithm, systematically
transformed.

**Unioning over cases.** The network detects two cases separately, then takes a
union to build an invariant unit. In the dog-head circuit, three layers maintain
two mirrored pathways — heads facing left, heads facing right — which at each
step **inhibit each other**, sharpening the contrast, before a final layer
responds to both [olah-2020 §Circuit 2].

Two details make this more interesting than it first sounds. First, because the
pathways inhibit one another, the circuit has XOR-like properties — this is not
just an OR over two detectors. Second, the authors are openly surprised gradient
descent found it: the network could have built an invariant neuron the lazy way,
by not caring where the eyes and snout were and looking for a jumble of parts.
Instead it carved the cases apart and handled them separately.

**Superposition.** A feature spread across neurons primarily doing something
else. See [[superposition]].

## What it licenses

Motif claims are claims about *form*, not about function or necessity. Naming a
pattern is a compression of things already observed; it predicts where to look
next, and predicts nothing about what a component does in a given model.

The risk is specific and worth naming, because motifs are the most
pattern-matchable idea in the paper: a motif vocabulary makes it very easy to
see a motif. "Unioning over cases" is loose enough to describe a great many
things if you are not careful about what would count as *not* it. The paper's
own discipline — introduce each motif through a specific circuit whose weights
were actually inspected — is the guard against this, and it should be copied
rather than the vocabulary alone.

## Where it's contested

Not contested in this source; it is offered as a research direction with three
instances. What is not offered is any criterion for when a motif is real versus
imposed. The systems-biology literature it borrows from has statistical tests
for motif over-representation against a null model of randomly rewired graphs;
no analogue is proposed here.

## What this project does with it

- **Self-repair is arguably a motif**, and reading it that way sharpens the
  spine. D-002 splits apparent self-repair into a mechanical component
  (LayerNorm rescaling) and a compensatory one (backup heads). "Backup" as a
  recurring wiring pattern is exactly a motif claim; "LayerNorm rescaling" is
  not a motif at all but an architectural side effect. The distinction the
  project is built on is partly the distinction between a motif and a
  mechanical artifact.
- **E5 is a motif question.** Whether components implicated in grammar overlap
  with those implicated in factual recall is asking whether sharing is a
  recurring pattern. The warning above applies with force — E5 is described in
  the roadmap as "easy to over-read", and a motif vocabulary would make it
  easier still.
- **The demand for a null model is the useful import.** Before naming any
  pattern across E3's heatmaps, ask what the pattern would look like if there
  were nothing there. Systems biology asks this routinely; Zoom In does not.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Circuit 1 · Circuit 2 · Circuit 3 · Circuit Motifs · Glossary.

## Open questions

- What is the null model for a motif claim in a transformer? Randomly rewired
  graphs do not obviously translate to a residual-stream architecture. If E5 is
  ever attempted, this needs an answer first.
