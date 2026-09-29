---
title: Phase change (induction bump)
type: phenomenon
status: drafted
sources: [olsson-2022]
first-needed: E6
updated: 2026-09-08
---

# Phase change (the induction bump)

## In one sentence

A narrow window early in training during which in-context learning ability
appears abruptly, induction heads form, the loss curve visibly bends, and the
model's trajectory in function space pivots — all at once, in every model with
more than one layer.

## Why it exists

It is the paper's central piece of evidence, and it exists as a concept because
it is the point where a *macroscopic* observable (a bump in the loss curve) and
a *microscopic* one (a particular head forming) can be watched happening
together. The authors describe it as a potential "Rosetta stone" linking
mechanistic interpretability, learning dynamics and scaling laws
[olsson-2022 §Linking Learning Dynamics, Scaling Laws, and Mechanistic
Interpretability].

The reason to care here is narrower: E6 proposes to watch a circuit form over
training, and this is the published account of what that looks like.

## Intuition, then mechanism

The name is borrowed from physics — "perhaps analogous to e.g. ice melting"
[olsson-2022 §Argument 1] — and carries the useful implication that a
continuous change in one parameter produces a discontinuous change in the
system's behaviour.

**Where the analogy breaks.** No claim of an actual critical point is made, and
none is measured. What is shown is co-occurrence in a window, with the window's
width depending on checkpoint spacing. For the full-scale models there are only
14–15 snapshots in the whole training run [olsson-2022 §Model Details], which
the authors themselves count as a weakness: "co-occurrence when one only has 15
points in time is less surprising and weaker evidence" [olsson-2022 §Assessing
the Evidence].

**What co-occurs**, as the paper lists it [olsson-2022 §Argument 1]:

1. In-context learning score sharply improves.
2. Induction heads form.
3. The loss curve shows a bump — "the only place in training where the loss is
   not convex".
4. The model's trajectory in per-token-loss space abruptly changes direction
   (visible in the first two principal components).

The one-layer model is the control and fails all four, which is what the
induction-head hypothesis predicts, since induction requires composition across
layers.

**One-line checkpoint:** four unrelated-looking measurements move together in
one window, and only in models that can express induction heads.

## Precisely

- **When.** "Roughly 2.5 to 5 billion tokens" [olsson-2022 §Argument 1]; for
  large models this is "maybe 1–2% of the way through training". *Recorded
  discrepancy:* §Model Details gives "approximately 1 – 3 billion tokens in the
  small models". The two ranges are stated in different sections and are not
  reconciled in the text. Quote the section, not a single number.
- **How much.** Under 0.15 nats of in-context learning before, roughly 0.4 nats
  after, constant thereafter and roughly constant across model sizes. "Over 75%
  of final in-context learning forms in this window" [olsson-2022 §Assessing the
  Evidence].
- **Not a scheduled artifact.** The window does not coincide with a learning
  rate, warmup or weight decay change. Weight decay was reduced at 4750 steps
  (~5e9 tokens), producing a visible deviation *after* the phase change; learning
  rate warmup ramps over the first 1.5e9 tokens [olsson-2022 §Model Details].
- **Not dataset-specific.** Small models retrained on a books-only dataset show
  the phase change developing the same way. But all models trained on a given
  dataset "saw the same examples in the same order" [olsson-2022 §Model Analysis
  Table], so data-order confounds are not ruled out.
- **The measurement substrate.** 34 decoder-only transformers, one training run
  each; 200 snapshots every 50 steps for the small models (10,000 steps ≈ 10e9
  tokens), 14–15 snapshots at 2× step spacing for the full-scale ones; per-token
  losses collected on a fixed set of 10,000 examples of 512 tokens
  [olsson-2022 §Model Analysis Table, §Data Collection].

**The interventional version** [olsson-2022 §Argument 2]. Rather than only
observing, the authors change the architecture so induction becomes expressible
in one layer: a "smeared key" model with a trainable $\alpha$ per head, using
$\sigma(\alpha) \in [0,1]$ to interpolate each key with the previous position's key,
$k_j = \sigma(\alpha) \cdot k_j + (1 - \sigma(\alpha)) \cdot k_{j-1}$ (the first token is unchanged). One-layer
smeared-key models then *do* develop in-context learning, and deeper ones
develop it earlier. This is the strongest causal handle in the paper outside the
ablations, and it is still graded Medium/Interventional for small models and
Weak for large.

**A second, stranger signature** [olsson-2022 §Phase Change Effect on Loss
Derivatives]: plotting the derivative of loss with respect to log(elapsed
tokens), the ordering by model size *inverts* at the phase change — small models
improve faster before it, large models after.

## What it licenses

Observing co-occurrence licenses: *these four measurements move together in this
window, across these 34 models.* It is correlational. The paper says so in every
table cell for Argument 1 (Medium, Correlational) and states the leading
confound itself:

> Perhaps the phase change is really the point at which the model learns how to
> compose layers through the residual stream, enabling both induction heads and
> potentially many other mechanisms that also require composition
> [olsson-2022 §Assessing the Evidence].

That is a shared-latent-variable objection, and it is not answered. A weaker,
carefully stated conclusion the authors do draw: the claim that induction heads
account for most in-context learning **at the transition point** is better
supported than the claim that they do so **at the end of training**.

## What this project does with it

- **E6's subject matter.** O-010 asks what quantity E6 tracks per checkpoint.
  This page is the prior art: candidate 2 (behavioural head scores over
  checkpoints) is literally this paper's figure, which is why it is the
  reproducible option, and candidate 1 (the E3 lesion map per checkpoint) is a
  new observable to be justified against it.
- **A caution for O-010's visualisation question.** The paper's own
  dimensionality reduction is PCA over per-token loss vectors where *a point is
  a checkpoint*, not a head — and even then it is presented as "a useful
  visualization for capturing the highest-level story", not as evidence. That is
  a sober precedent for the concern already recorded in O-010 about UMAP
  manufacturing clusters over ~100 heads.
- **O-004 gets sharper.** Checkpoint density is not a detail: the authors' own
  strongest results come from 200 linear snapshots, and their weakest from 15
  exponential ones. Whatever Pythia offers in the formation window should be
  compared against those numbers before E6 is planned.
- **Nothing here is in the minimum shippable project** (R0, R1, E0–E4). This
  page is `first-needed: E6` and should not pull scope forward.

## Sources

- [olsson-2022] Olsson et al., "In-context Learning and Induction Heads",
  Transformer Circuits Thread, 8 March 2022.
  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
  Sections cited: Argument 1 · Looking at the Phase Change More Closely ·
  Assessing the Evidence · Argument 2 · Model Analysis Table · Model Details ·
  Phase Change Effect on Loss Derivatives · Linking Learning Dynamics, Scaling
  Laws, and Mechanistic Interpretability.

## Open questions

- **Does the phase change appear in Pythia at all, and at what token count?**
  The models here are Anthropic's, with an 8192-token context and a $2^{16}$
  vocabulary — not Pythia's setup. Feeds O-004.
- Is the loss bump detectable in a public model's published loss curve, or only
  in the derived per-token analysis? Determines whether E6 can check its
  checkpoint set cheaply before committing to it.
