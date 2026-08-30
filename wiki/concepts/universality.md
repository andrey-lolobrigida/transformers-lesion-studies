---
title: Universality
type: concept
status: drafted
sources: [olah-2020]
first-needed: E6
updated: 2026-08-30
---

# Universality

## In one sentence

The hypothesis that **analogous features and circuits form across different
models and tasks** — the third of Zoom In's three speculative claims, and the
one its authors say they cannot yet support with more than anecdote.

## Why it exists

It determines what kind of research is worth doing. The paper's argument for
why it matters is better than any paraphrase:

> imagine a world where every species had cells with a completely different set
> of organelles and proteins. Would it still make sense to study cells in
> general, or would we limit ourselves to the narrow study of a few kinds of
> particularly important species of cells? [olah-2020 §Claim 3]

If universality holds strongly, you can imagine a "periodic table of visual
features" catalogued across models, and a finding in one model is a finding
about networks. If it fails, interpretability becomes the study of a handful of
commercially important models, and you had better hope they stop changing every
year.

Unlike the first two claims, the paper notes this one failing would not be fatal
to circuits research — but it would change its form entirely.

## Intuition, then mechanism

The intuition is **convergent evolution**. It is widely accepted that the first
layer of any vision model trained on natural images learns Gabor filters
(oriented edge-and-texture detectors). Once you accept that later layers hold
meaningful features too, why would the convergence stop at layer one? And if
analogous features form at several layers, why wouldn't they connect the same
way [olah-2020 §Claim 3]?

**Where that intuition is weaker than it sounds — and the paper says so.**
Universality, also called *convergent learning*, has been suggested before, and
prior work has shown different networks developing highly correlated neurons
and similar hidden representations. The authors call this suggestive but not
definitive, and give the reason: **correlation between two features does not
make them the same feature.** A fur-texture detector and a sophisticated
dog-body detector could be highly correlated while being importantly different
things. Adopting the feature-skeptic position, correlational evidence does not
close the case.

What would close it, in their view: characterise several features precisely,
then demonstrate that *those* features — not merely correlated ones — form
across many models; then find analogous features across several layers of
multiple models and show the same weight structure forms between them.

## What it licenses

Almost nothing yet, and the paper's candour on this point is the most useful
thing on the page:

> Unfortunately, the only evidence we can offer today is anecdotal: we simply
> have not yet invested enough in the comparative study of features and circuits
> to give confident answers. [olah-2020 §Claim 3]

What they do report: a couple of **low-level** features appear to form across a
variety of architectures (AlexNet, InceptionV1, InceptionV3, residual networks),
in models trained on Places365 rather than ImageNet, and repeatedly in vanilla
convnets trained from scratch on ImageNet.

So the licensed claim is narrow: *some low-level vision features recur across
architectures and training sets*. The authors state directly that whether this
apparent universality is "the exception or the rule" is unknown.

Any stronger use — transferring a circuit-level finding from one model to
another, or treating a result on GPT-2 small as a result about transformers —
is not licensed by this source.

## Where it's contested

- **By its own authors**, on evidence. See above.
- **The biological extension is speculation, labelled as such.** The paper
  raises the possibility that biological networks learn similar features, notes
  that curve detectors are believed to exist in biological vision, and offers a
  genuinely strong test: if an artificial network predicted a feature previously
  unknown in biology which was then found there, that would be extremely strong
  evidence. High-low frequency detectors are floated as a candidate. This is
  offered as an exciting possibility, not a result.

## What this project does with it

- **E6 is a universality experiment in disguise.** "Does a circuit appear at
  the same point across training?" and Tigges et al.'s reported consistency
  across training and scale are the language-model version of this claim. The
  Zoom In framing — that the answer determines what *form* of research makes
  sense — is the reason E6 is worth more than its size suggests.
- **It sets the ceiling on every other phase's claims.** Everything through E4
  runs on GPT-2 small. Without universality, an E3 heatmap is a fact about one
  124M-parameter model from 2019 and nothing more. This should be stated in the
  writeup rather than left for a reader to infer.
- **The correlation caveat transfers verbatim.** Two heads in two models that
  respond similarly are not thereby the same head. Any cross-model claim needs
  the stronger form of evidence the paper describes — same features *and* same
  weight structure between them.

## Sources

- [olah-2020] Olah et al., "Zoom In: An Introduction to Circuits", Distill,
  10 March 2020. https://distill.pub/2020/circuits/zoom-in/
  Section cited: Claim 3.

## Open questions

- Has the language-model literature answered this since 2020? Tigges et al.
  2024 (R3, arXiv 2407.10827) reports circuit analyses are consistent across
  training and scale, which is the closest thing to an answer in the reading
  list. Resolve at R3 — and note that if it holds, E6's framing shifts from
  "does this happen" to "when".
- Does universality hold *across ablation methods*? An odd-sounding question,
  but D-006 says the ablation defines the task, so a circuit found under
  zero-ablation and one found under resample-ablation in the same model may not
  be the same object. That is a universality problem inside a single model.
