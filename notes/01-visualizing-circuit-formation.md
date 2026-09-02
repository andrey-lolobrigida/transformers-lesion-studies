# 01 — Visualizing circuit formation over training

*2026-09-02, while reading Olsson et al. (R0). Scratch, not a plan. The
structured version is O-010 in `docs/04-decisions.md`.*

## The idea as it arrived

Olsson et al. claim induction heads emerge at a particular point in training,
and that the phase is visible in the loss curves. So: is there anything we can
*visualize during the training run*? What I saw in my head was a clustering
picture from UMAP or t-SNE, but through time — clusters evolving as training
proceeds. The caveat, in my own words: I don't have a clue what exactly we'd
be visualizing. Something about the weights? Partial derivatives or
sub-vectors of the gradient? Something that hints at the shape of the
optimization surface?

## What the conversation added

- The idea has a home already: E6 in the roadmap. This is filling in a
  sketch, not opening a new direction.
- The fuzzy part is "what is a point?" Dimensionality reduction needs a set
  of points. Head, neuron, or checkpoint — pick one and the quantity follows.
- Olsson's phase change is in a *derived* score (loss late in context minus
  loss early in context), not raw loss. Check this against the paper.
- Ranked observables: lesion map per checkpoint > behavioural head scores >
  weight-only composition scores > gradient/loss-surface geometry.
- UMAP on ~100 heads manufactures clusters. Two named scores on a plain
  scatter, animated over checkpoints, is the honest version.
- "Shape of the optimization surface" is its own programme. See
  `02-loss-surface-programme.md`.

## Things I'd want to know before this becomes a plan

- Do Pythia's checkpoints cover the formation window densely enough? (O-004)
- Does "during the training run" mean literally training something small
  ourselves, or reading Pythia checkpoints? The former crosses the
  "ablation is an inference problem" framing in `docs/00-motivation.md`.
