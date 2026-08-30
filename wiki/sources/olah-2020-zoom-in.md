---
key: olah-2020
title: "Zoom In: An Introduction to Circuits"
authors: Olah, Cammarata, Schubert, Goh, Petrov, Carter
year: 2020
venue: Distill (Circuits thread)
doi: 10.23915/distill.00024.001
arxiv: —                     # Distill-native; arXiv not searched, absence unverified
url: https://distill.pub/2020/circuits/zoom-in/
local: —
phase: R0
extraction: complete
feeds:
  - circuit
  - feature
  - polysemanticity
  - superposition
  - universality
  - circuit-motif
  - interpretability-as-natural-science
  - feature-claim-evidence
---

# Source card — Olah et al. 2020

Published 10 March 2020. All authors at OpenAI at time of publication. First
article of the Distill **Circuits thread**; explicitly an overview essay whose
detailed claims are deferred to later articles in the thread.

Model studied: **InceptionV1**, a convolutional image classifier. Vision, not
language — every page fed by this source carries a note on what transfers.

## Structure

| Section | What it holds |
|---|---|
| Three Speculative Claims | The Schwann cell-theory framing; why a strong falsifiable claim beats a hedged one |
| Claim 1: Features | Curve detectors, high-low frequency detectors, pose-invariant dog head; the seven arguments; polysemantic neurons |
| Claim 2: Circuits | Curve detector circuit, oriented dog head detection, cars in superposition; circuit motifs |
| Claim 3: Universality | Convergent learning; the authors' concession that their evidence is anecdotal |
| Interpretability as a Natural Science | Kuhn, pre-paradigmatic fields, falsifiability as the evaluation standard |
| Closing Thoughts | The microscope and *Micrographia* |
| Glossary | Formal definitions: circuit, direction, feature, family, motif, pure/polysemantic |

## Extraction log

**2026-08-30 — complete.**

Read in full from the live article. Extracted to six concept pages and one
method page (see `feeds`). Fifteen terms proposed for `docs/05-glossary.md`.

Deliberately left:

- **Feature visualization as a technique.** Argument 1 of seven is recorded on
  [[feature-claim-evidence]], but no page was opened for the method itself — it
  is input-optimisation for images and has no clean equivalent for discrete
  tokens. Fails the "would getting it wrong change an experiment" test for this
  project.
- **The InceptionV1 architectural details** (1×1 bottleneck followed by 3×3 or
  5×5 convolution; the paper multiplies these out and treats the pair as one
  low-rank weight matrix, noting this ignores a ReLU). Not portable.
- **The Kuhn/Micrographia framing** was extracted only as far as it bears on
  evidentiary standards, on
  [[interpretability-as-natural-science]].

Not resolvable from this source, carried forward as open questions on the pages
themselves: how common polysemanticity is; whether superposition occurs at the
level of attention heads; how a weight-read circuit relates to an
ablation-identified one.

## Note on citing

Distill articles are section-titled but not numbered. Citations on wiki pages
use the section heading verbatim: `[olah-2020 §Claim 3]`, `[olah-2020 §Circuit
1]`. The DOI above is taken from the article's own metadata and is verified. No
arXiv version was looked for — the `arxiv: —` field records "not checked", not
"does not exist".
