---
title: Evidence for a feature claim
type: method
status: drafted
sources: [olah-2020]
first-needed: E3
updated: 2026-08-30
---

# Evidence for a feature claim

## In one sentence

Seven arguments that Olah et al. offer for the claim "this unit is a curve
detector" — a general checklist for what it takes to say a component detects
something, rather than that it correlates with something.

## Claim-licence block

| | |
|---|---|
| **Answers** | *What causes this component to activate?* Collectively, the seven arguments support a claim about the unit's response profile and how it is built and used. |
| **Does NOT answer** | Whether model behaviour *depends* on the unit. None of the seven is an ablation. A fully evidenced feature claim still says nothing about necessity. |
| **Confounds** | Arguments 1–4 are stimulus-response only and cannot distinguish a detector from something reliably correlated with it — the paper names this gap explicitly. Arguments 5–7 depend on the features feeding in already being understood, so the evidence is recursive and can rest on unexamined ground. |
| **Always log** | Which of the seven were actually run. A claim supported by feature visualization alone is not the same claim as one supported by all seven, and in a writeup they read identically unless the difference is stated. |

## Why it exists

The paper needs to defend the claim that a unit is a curve detector against a
serious skeptical position — that apparently meaningful neurons are
misunderstood, and that networks trade in texture and local structure rather
than concepts [olah-2020 §Claim 1]. Asserting it from feature visualizations
alone would not survive that objection.

So they enumerate the arguments instead, and note that **none of them are curve
specific**: they are offered as a general toolkit for testing our understanding
of any feature. Three of them — dataset examples, synthetic examples, and
tuning curves — are described as classic methods from visual neuroscience
[olah-2020 §Example 1].

That lineage matters for this project. `docs/00-motivation.md` adopts the
neuroscience framing deliberately; this is the same borrowing, one level down,
and the same question applies: does the standard survive the transfer?

## The seven arguments

Verbatim in substance from [olah-2020 §Example 1]. Arguments 1–4 are
stimulus-based; 5–7 are circuit-based.

| # | Argument | What it shows |
|---|---|---|
| 1 | **Feature visualization** — optimise an input to make the unit fire | Establishes a *causal* link: everything in the resulting image was added in order to increase the activation |
| 2 | **Dataset examples** — which real inputs make it fire most | Tests use in practice, and whether a second class of stimulus also triggers it |
| 3 | **Synthetic examples** — generated curves varying orientation, curvature, background | Responds only near the expected orientation; does not fire strongly for straight lines or sharp corners |
| 4 | **Joint tuning** — rotate a dataset example that makes it fire | It gradually stops firing as the *next* orientation's detector starts. Shows the family detects rotated versions of one thing, tiling 360° |
| 5 | **Feature implementation** *(circuit)* — read the incoming weights | A curve-detection algorithm can be read off the weights, with no second alternative cause of firing visible |
| 6 | **Feature use** *(circuit)* — inspect downstream clients | Its clients are features that naturally involve curves (circles, spirals, 3D curvature), using it as expected |
| 7 | **Handwritten circuits** *(circuit)* — hand-set weights to reimplement it | A cleanroom reimplementation is an understandable curve-detection algorithm and significantly mimics the original unit |

Note the pairing in 1 and 2. Feature visualization establishes causality;
dataset examples test practice and check for a second stimulus class. The paper
says the combination of the two alone is already quite a strong argument
[olah-2020 §Example 3] — neither is strong alone, and they fail in different
directions.

## What the authors claim it establishes — and what it doesn't

Stated with unusual care, and worth copying as a template for how to write up a
result [olah-2020 §Example 1]:

> The above arguments don't fully exclude the possibility of some rare secondary
> case where curve detectors fire for a different kind of stimulus. But they do
> seem to establish that (1) curves cause these neurons to fire, (2) each unit
> responds to curves at different angular orientations, and (3) if there are
> other stimuli that cause them to fire those stimuli are rare or cause weaker
> activations.

That is what a properly bounded claim looks like: three numbered things
established, one named residual possibility not excluded. Compare with epistemic
rule 1 in `CLAUDE.md`, which demands the same shape for ablation results.

The paper then appeals to neuroscience's evidentiary standards as the
benchmark. That appeal is load-bearing and is not itself argued for.

## Where it's contested

- **Cost scales badly with abstraction.** The authors concede that for
  higher-level features, arguments 1–4 become a lot of effort — a 3D model had
  to be built to generate dog heads at varying angles [olah-2020 §Example 3].
  Their fallback is the circuit-based arguments, which are cheaper but rest on
  the upstream features already being understood.
- **Arguments 5–7 are unavailable early.** Reading a circuit off the weights
  requires knowing what the inputs mean. At the start of a project nothing is
  known, so only the weaker half of the toolkit is available exactly when the
  most consequential framing decisions get made.
- **Argument 7 is the strongest and the rarest.** A cleanroom reimplementation
  is close to a proof of understanding, and it appears once in the paper.

## What this project does with it

The direct transfer is **argument 6, feature use**. E3 will single out heads
from ablation heatmaps, and `CLAUDE.md` already requires that any head named as
important be verified by activation patching first. Asking additionally what a
head's downstream clients are — and whether they use it in a way consistent
with the story being told — is a cheap second check in the same spirit.

**Arguments 1–4 mostly do not transfer.** Feature visualization by input
optimisation is a vision technique that has no clean equivalent for discrete
tokens. Their language-model analogues are different tools: max-activating
dataset examples for 2, templated prompt sweeps for 3.

**Argument 7 is worth remembering for O-006.** The open question about pulling
knock-in calibration forward — planting a mechanism and checking the harness
recovers it — is argument 7 run in reverse, and this page is prior art for the
idea that reimplementation is the strongest evidence available.

The genuinely portable lesson is the accounting itself: **say which arguments
you ran.** A claim resting on one is written the same way as a claim resting on
seven unless the difference is recorded.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Sections cited: Claim 1 · Example 1 · Example 2 · Example 3.

## Open questions

- What are the language-model equivalents of arguments 3 and 4? Templated
  prompts and systematic corruption sweeps are the obvious candidates, which
  connects to `O-003` (whether E2/E3 should sweep corruption schemes the way
  they sweep ablation methods).
- Does this project want a per-claim record of which arguments were run,
  analogous to the mean-ablation dataset size under epistemic rule 4? Decide in
  R1 when writing `docs/01-methods.md`.
