---
title: In-context learning
type: concept
status: drafted
sources: [olsson-2022]
first-needed: E2
updated: 2026-09-08
---

# In-context learning

## In one sentence

In-context learning is a model getting **better at predicting tokens the further
into the context it is** — measured here not as few-shot task performance but as
the drop in loss between an early and a late token index.

## Why it exists

There are two incompatible things called in-context learning in the literature,
and the paper's first move is to pick one and say why [olsson-2022 §In-Context
Learning]:

- **The micro conception (Brown et al.)** — few-shot learning of a specific
  task: prompt the model with several examples of addition or translation and
  measure whether it does the task. This is the conception that got the
  community's attention, because it changes the economics of model training.
- **The macro conception (Kaplan et al.)** — observe the loss at different token
  indices, and measure how much better prediction gets as context accumulates.

Olsson et al. use the macro one. The stated reason is generality: it does not
depend on the researcher's choice of task. The stated drawback is admitted in
the same breath — it "fails to isolate specific behaviors of interest".

The paper also flags the vocabulary problem. "Metalearning" is sometimes used
as a synonym, but it smuggles in the stronger claim that the model is learning
*how* to do a new thing rather than *locating* an ability it already has — an
implication the authors call "controversial and not entirely precise".

## Intuition, then mechanism

**The intuition** is unglamorous on purpose: a sequence model is built to use
earlier elements to predict later ones, so of course loss falls with context.
The paper's own framing is that this becomes interesting only when it gets good
enough to be *used* — for specifying tasks, giving instructions, asking for a
pattern match — at which point it is worth treating as a phenomenon in its own
right rather than as the definition of sequence modelling.

**Where the intuition breaks, and it breaks in a way that matters for E3.**
"Loss goes down with context" invites reading the in-context learning score as
a competence measure, where more is better and damage should reduce it. It is
not. It is a *difference* between two losses, so anything that makes the model
worse at early-context prediction raises it. The paper hits this directly:
ablating most non-induction heads **increases** the in-context learning score,
and the explanation offered is that some tokens can be predicted either by
"normal prediction" or by in-context learning, so breaking normal prediction
leaves in-context learning more to explain [olsson-2022 §Argument 3].

**One-line checkpoint:** the score measures a *gap*, and a gap widens when
either side moves.

## Precisely

The measurement used throughout [olsson-2022 §In-Context Learning]:

> **In-context learning score:** the loss of the 500th token in the context
> minus the average loss of the 50th token in the context, averaged over dataset
> examples.

Computed on a length-512 context, over 10,000 dataset examples of 512 tokens,
with the example set held fixed across every snapshot and every model
[olsson-2022 §Data Collection]. The indices were chosen "somewhat arbitrarily":
500 is near the end of the context, 50 is far enough in that basic properties of
the text are established.

**A sign-convention warning.** As literally defined — later loss minus earlier
loss — the quantity is *negative* when the model is doing in-context learning,
since later tokens are easier. The reported magnitudes are positive: "less than
0.15 nats of in-context learning" before the phase change, "roughly 0.4 nats"
after [olsson-2022 §Argument 1]. So the reported score is the negation, or the
plots are sign-flipped. Nothing in the text resolves it. **If this project
computes an in-context learning score, fix the sign explicitly in code and state
it next to every number**; a silently flipped sign here turns "ablation
destroyed in-context learning" into "ablation improved it".

The paper checks robustness to the arbitrary indices: redefining the score
against the final token (8192) and other indices leaves the conclusions intact
[olsson-2022 §Seemingly Constant In-Context Learning Score].

## What it licenses

Measuring this score licenses a statement about **how much better a model
predicts late tokens than early ones, on this dataset, at these two indices.**

It does not license:

- **"The model can do few-shot learning."** That is the other conception, and
  the paper is careful never to equate them. A model could improve its
  late-context loss purely by repeating names it has already seen.
- **"In-context learning is constant across model sizes."** This *is* what the
  score shows — the post-phase-change value is about 0.4 nats regardless of
  size — but the authors argue it is partly an artifact of the baseline moving:
  reducing loss by a fixed amount from a lower starting point is harder, so
  "the relative loss between token 50 and token 500 likely represents harder and
  harder bits over the course of training" [olsson-2022 §Assessing the
  Evidence]. Equal score does not mean equal mechanism.
- **Any attribution to a component.** That needs the ablation
  [[pattern-preserving-ablation]], and even then the increase-under-damage
  behaviour above has to be reasoned about first.

## Where it's contested

- **The constancy is unexplained by the authors.** They call it "one of the
  stranger observations in this paper" and offer a partial account: large models
  gain most of their advantage over small ones in the *first ten tokens* of
  context, then improve by a roughly fixed amount over the rest. Their own
  verdict is that this makes it "strange rather than shocking"
  [olsson-2022 §Seemingly Constant In-Context Learning Score].
- **Whether induction heads are the mechanism is the paper's thesis, not a
  finding.** The evidence tables grade it Strong/Causal only for small
  attention-only models; for large models it is Medium/Correlational
  [olsson-2022 §Arguments that induction heads are the mechanism...].
- **Mesa-optimisation is explicitly not observed.** In-context learning has been
  speculated to be an internal optimiser; the paper's position is that the
  mechanism, at least in small models, is induction heads, and "we did not
  observe any evidence of mesa-optimizers" [olsson-2022 §Safety Implications].
  Recorded because the overclaim is common; `CLAUDE.md` forbids making it here.

## What this project does with it

- **Not the default metric.** Epistemic rule 5 makes logit difference the
  default and requires a written reason to use loss. This score is a loss
  difference, so using it needs that written reason — the reason being that E2
  reproduces a published result stated in these terms. Outside that
  reproduction, prefer logit difference.
- **A worked warning for E3 battery design.** This is a metric that *improves*
  when the model is damaged, for a comprehensible reason. O-009 asks whether
  every battery item needs a stated clean-accuracy gate; this suggests a second
  cheap rule — state, per metric, which direction damage is expected to move it,
  and treat an unexpected sign as a result to investigate rather than a bug to
  suppress.
- **E1 note.** If an in-context learning score is implemented, the artifact
  should record the two token indices, the context length, the number of
  examples, and the sign convention.

## Sources

- [olsson-2022] Olsson et al., "In-context Learning and Induction Heads",
  Transformer Circuits Thread, 8 March 2022.
  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
  Sections cited: In-Context Learning · Argument 1 · Argument 3 · Assessing the
  Evidence · Seemingly Constant In-Context Learning Score · Safety Implications ·
  Data Collection.

## Open questions

- **Which sign convention does the published figure use?** Resolvable only by
  reading the plot axes; worth doing before E2 quotes a number.
- Does this project want an in-context learning score in the battery at all, or
  only as an E2 reproduction target? Decide in E1.
