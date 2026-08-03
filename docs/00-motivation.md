# 00 — Motivation and framing

## The project in one paragraph

Take a small pretrained transformer, disable individual components — attention
heads, neurons, whole layers, specific residual-stream positions — and measure
how behaviour degrades across different task types. From the pattern of damage,
build a functional map: which components matter for grammatical agreement,
which for factual recall, which for in-context copying. This is the lesion
method from neuroscience, run on a system where the intervention is exact,
perfectly repeatable, and reversible.

## Why this fits the constraints

Ablation is an inference problem, not a training problem. Running a 124M–410M
parameter model forward needs roughly 1–2 GB of VRAM; an 8 GB card has ample
headroom, and most of the compute goes to running many forward passes rather
than any single expensive one. Training only enters if the project extends to
studying how circuits form (roadmap phase E6), and even then TinyStories-scale
models train in hours on this hardware.

The practical implication: the bottleneck on this project is not compute. It's
experimental design and knowing when you've fooled yourself. Budget attention
accordingly.

## The neuroscience framing, and its limits

The analogy is genuinely useful for orientation. Ablation maps to lesion study;
out-of-distribution probing maps to violation-of-expectation paradigms;
observing unprompted behaviour maps to ethology. Treating the model as a
specimen rather than a product is a productive reframing, and most of the
tooling in this space was built by people thinking that way.

But the analogy has failure modes, and they need to be written down before they
cause problems rather than after.

**Diaschisis.** The oldest problem in lesion studies: you damage region A,
region B stops working, and B was fine — it just lost its input. Transformers
have a version of this that is arguably worse. Every component downstream of an
ablation reads a changed residual stream, so a "local" lesion is never local.
The subject is not cleaner than a brain here; it's dirtier, with the
consolation that the dirt is measurable.

**Off-distribution intervention.** Ablation puts the model into internal states
that no input could produce. The model was never trained to behave coherently
under these conditions, so some of what you observe is the model's response to
an impossible situation rather than a readout of what the ablated component
did. This is not a minor caveat; it drives a substantial part of the self-repair
phenomenon this project is built around.

**Phrenology risk.** A heatmap of loss-deltas across heads is the most
persuasive artifact this project can produce and the easiest to over-read. It
will look like a functional map whether or not the underlying function is
localised. Any such figure ships with its caveats attached, not appended later.

**The worm.** *C. elegans* has had a complete connectome since 1986 — 302
neurons, every synapse mapped — and behaviour still cannot be predicted from
the wiring diagram. Full read access to a system is not the same as
understanding it. This is the relevant cautionary case for anyone claiming that
weight access makes interpretability easy.

## What the project is trying to be

**Reproduction-first research.** Replicate known results carefully, then map
where they stop holding: under different ablation methods, different prompt
distributions, different models. In an area with documented problems around
methodological robustness, establishing where a published result's boundaries
lie is a contribution, not a consolation prize.

This mode also tends to generate novel questions on its own. You reproduce
something, notice an unturned knob, and turn it. That's the intended path to
anything original here — not a separate search for novelty.

**What it is not trying to be:** a survey, a tool, a benchmark submission, or a
contribution to the sparse-autoencoder frontier. Those are all reasonable
projects; they are different projects, with different tooling burdens and
different competition.

## Model zoo

| Model | Size | Role |
|---|---|---|
| GPT-2 small | 124M | Primary subject. Almost every classic result was found here, so there is always a published number to check against. |
| Pythia | 70M / 160M / 410M | Secondary. Public checkpoints saved throughout training make "when did this appear?" answerable. Relevant only from E6. |
| TinyStories | 1M–33M | Cheap enough to ablate on CPU and to train from scratch. Useful for pipeline testing and as a contrast case. |

Escape hatch if a question genuinely needs scale: `nnsight` with `remote=True`
runs interventions on large hosted models with the same code. Not needed for
anything currently planned.

## Scope guard

The smallest version that is still a complete, honest piece of work: reading
phases R0–R1, plus experiment phases E0–E4 on GPT-2 small. That is a functional
map, a verified reproduction, and one careful extension. It ships as a blog
post and a repo.

Everything after E4 is optional and gets planned when reached, not before.
