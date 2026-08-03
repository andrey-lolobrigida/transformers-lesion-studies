# Lesion Studies for Transformers

Disabling parts of a small language model on purpose, and measuring carefully
what breaks.

The method is borrowed from neuroscience: damage a component, observe the
deficit, infer the function. Transformers make a better subject than brains in
some respects — the intervention is exact, repeatable, and reversible — and a
worse one in others, since ablation pushes the model into internal states no
input could produce, and every downstream component sees the disturbance.

## What's here

This is a **reproduction-first** project. The plan is to replicate known
results carefully, then map where they stop holding: under different ablation
methods, different prompt distributions, different models. Boundary-mapping is
the goal; anything novel is expected to emerge from it rather than be hunted
directly.

The working spine is self-repair after ablation, with the mechanical component
controlled for — separating the part of a model's post-lesion recovery that is
a side effect of layer normalisation from the part that is actual compensation.

Primary subject: GPT-2 small.

## Status

Planning. No code yet. Current phase: R0 (orientation reading).

## Documents

| File | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Operating manual: epistemic rules, conventions, what not to do |
| [`docs/00-motivation.md`](docs/00-motivation.md) | Why this project; where the neuroscience framing breaks |
| [`docs/01-methods.md`](docs/01-methods.md) | The methods, and what each measurement licenses |
| [`docs/02-roadmap.md`](docs/02-roadmap.md) | Reading phases R0–R3, experiment phases E0–E6 |
| [`docs/03-reading-list.md`](docs/03-reading-list.md) | Papers, grouped by the phase that needs them |
| [`docs/04-decisions.md`](docs/04-decisions.md) | Dated decision log, open questions, null results |
| [`docs/05-glossary.md`](docs/05-glossary.md) | Terms |
| [`docs/06-environment.md`](docs/06-environment.md) | Hardware, install order, gotcha log |
| [`docs/07-alignment-extension.md`](docs/07-alignment-extension.md) | A parked successor project, for after the core plan ships |

## Scope

The minimum complete version is reading phases R0–R1 plus experiment phases
E0–E4 on GPT-2 small: a verified reproduction, a functional map produced under
three ablation methods, and one careful extension. Anything past that gets
planned when reached.
