---
title: Pattern-preserving ablation
type: method
status: drafted
sources: [olsson-2022, elhage-2021, wang-2022, miller-2024]
first-needed: E1
updated: 2026-09-19
---

# Pattern-preserving ablation

## In one sentence

Ablate a head's **output** while freezing every attention pattern in the model
to its clean-run values, so the ablation cannot travel through the paths by
which that head shapes *where later heads look*.

## Claim-licence block

| | |
|---|---|
| **Answers** | Necessity, restricted to one route — "does behaviour break without this head's contribution to later components' *value* computations?" |
| **Does NOT answer** | Sufficiency (nothing is restored). Nor the head's total causal role: its influence on later heads' Q and K, and so on their attention patterns, is deliberately held fixed and is invisible to this measurement. |
| **Confounds** | Freezing patterns is itself an intervention — the model is run in a state it never occupies naturally, so the run is off-distribution in a second way on top of whatever the ablation value does. With MLPs the linearity that justifies the method is gone. Redundant heads plus LayerNorm rescaling can mask a head's importance (see below). |
| **Always log** | Which variant was used (full vs pattern-preserving), the ablation value (here: zero), the evaluation set size, seed, model revision hash. A number reported without the variant is not interpretable. |

## Why it exists

Ablating a head has two quite different downstream consequences, and ordinary
ablation fuses them:

1. The head's output no longer contributes to what later components *read* —
   its effect on later value vectors and on the logits.
2. The head's output no longer contributes to later heads' queries and keys, so
   later heads **attend somewhere else**. The model's routing changes.

Route 2 is exactly the mechanism by which an induction head works — a
previous-token head's output changes where the induction head looks. So an
experiment about attention-mediated computation that lets route 2 vary is
measuring a moving target.

Pattern-preserving ablation cuts route 2 by fiat. The paper notes this is only
possible because of a structural fact from Elhage et al. 2021: a head's
attention pattern and its output are computed by separable circuits — different
parameters, runnable in isolation [olsson-2022 §Data Collection (2)].

*Provenance, added 2026-09-14.* The freezing move is Elhage et al.'s "freezing
attention patterns trick": run once to collect every pattern, run again with
the patterns forced to the collected values, and the logits become a linear
function of the tokens [elhage-2021 §OV and QK Independence (The Freezing
Attention Patterns Trick)]. In an attention-only model, ablating one head with
patterns frozen is then exactly deleting that head's terms from the path
expansion — see [[path-expansion]]. That identity is what Olsson et al. say
"does not survive MLPs".

This is a **second axis** of ablation design, orthogonal to the zero / mean /
resample axis that D-006 already commits this project to sweeping. What gets
substituted, and what gets frozen, are independent choices.

## Precisely

The two variants, verbatim in substance [olsson-2022 §Data Collection (2)]:

**Full ablation**
- *Method:* run the model, replacing the ablated head's result vector with a
  zero vector.
- *Outcome:* all downstream computations are impacted, including all Q, K and V
  calculations and hence attention patterns.

**Pattern-preserving ablation**
- *Method:* run the model once, saving all attention patterns and discarding the
  logits. Run it a second time, replacing the ablated head's result vector with
  zero **and** forcing all attention patterns to the values recorded in the
  first run.
- *Outcome:* only downstream V calculations are affected. The ablated head's
  contribution to later layers' attention patterns is preserved.

Both are **zero-ablation** in the substitution sense. Neither is mean or
resample; this paper does not compare substitution values at all.

**The property that makes it principled — and its exact scope.** With the
attention pattern frozen, each head's action is purely linear. In an
*attention-only* model, a pattern-preserving ablation is therefore equivalent to
subtracting all terms containing that head from the output logits
[olsson-2022 §Data Collection (2)]. That equivalence is what licenses reading
the ablation as the head's contribution. **It does not hold once MLPs are
present** — the paper states this explicitly, and GPT-2 small has MLPs.

**Scale.** The model analysis table shows pattern-preserving results only; full
ablation results are in the appendix. Ablations were run on the small models
only, across all 200 snapshots — over 50,000 individual head ablations, each
evaluated on 10,000 examples. No ablations exist for the full-scale models: the
cost scales as O(N^1.33), since there are O(N^0.33) heads and each ablation
costs O(N) [olsson-2022 §Argument 3].

## What it licenses

For **attention-only** models, the paper is willing to say the measurement is
principled and near-complete: in-context learning must originate with attention
heads (the direct path term depends only on the present token and cannot
contribute), the relationship is almost linear up to LayerNorm rescaling, and so
ablations with frozen patterns are "a principled way to measure their
contribution" [olsson-2022 §Argument 3].

Two limits the authors state on their own result, both of which land squarely on
this project:

- **MLPs break the additivity.** "In models with MLPs, in-context learning could
  also come from interactions between MLP and attention layers... the
  relationship between the effect of the ablation on in-context learning and its
  true importance becomes more complicated." Their two named failure modes: an
  ablation may shift an MLP's activation statistics and "break" neurons by
  moving their effective bias without the head having a meaningful role; or an
  MLP mechanism relying on two heads may function on one when the other is
  removed. Their verdict: "we can't be fully confident that head ablations in
  MLP models give us the full picture."
- **Marginal effects can be masked.** "Our ablations measure the marginal
  effects of removing attention heads from the model. To the extent two heads do
  something similar and the layer norm before the logits rescales things, the
  importance of individual heads may be masked" [olsson-2022 §Argument 3].

That second sentence is **self-repair, named in 2022 as a measurement hazard**,
with both of its sources — redundancy between heads and LayerNorm rescaling —
already identified. It is a useful piece of provenance for E4: the phenomenon
the spine attacks was visible as a caveat well before it was studied directly.

## Where it's contested

- **Nothing in this source compares the two variants numerically.** The full
  ablation results are relegated to an appendix and no disagreement is reported
  or ruled out. Whether the axis matters empirically is, on this evidence,
  unknown.
- **Ablation can move a metric the "wrong" way for legible reasons.** Ablating
  most non-induction heads *increases* the in-context learning score
  [olsson-2022 §Argument 3]. See [[in-context-learning]]; the fault is in the
  metric's construction, not the ablation.
- **The paper's own earlier work ablated differently.** Elhage et al.'s
  ablation is a *term-importance* procedure: with all patterns frozen, replace
  every head's output with zero (step 2), then with the outputs saved from the
  previous step (step n), and difference the losses to get the marginal effect
  of all paths of order n. It manipulates every head at once and iterates over
  path order; it is not a single-head ablation, and the authors note it
  "only target[s] V-composition" because patterns are frozen [elhage-2021 §Term
  Importance Analysis]. The shared freezing choice makes the two procedures
  look more alike than they are [olsson-2022 §Data Collection (2)]. Full
  algorithm on [[path-expansion]].
- **Zero as a substitution value is not defended here.** The known objection —
  that zeroing moves the model off-distribution and distorts residual-stream
  norms — is not discussed in this paper. Wang et al. state it in one
  sentence and switch to mean ablation without a comparison [wang-2022 §2.1;
  [[mean-ablation]]]. R2 is where a comparison is expected.
- **Absent from the faithfulness literature's taxonomy** — added
  2026-09-19, and this is the O-011 R1 trigger. Miller et al.'s six-tuple
  (granularity · component type · value · positions · direction · set) has
  no axis for attention-pattern freezing, and the paper never mentions the
  intervention [miller-2024 §3.1, Table 1; [[ablation-methodology]]]. The
  nearest thing is *component type*: node, edge or branch ablation restricts
  which downstream destinations receive the change in the factorised or
  treeified view — a path restriction, and one they show is first-class
  (node vs edge moves IOI faithfulness from 87% to a median over 100%
  [miller-2024 §4.1]). But an edge ablation still lets the destination's
  attention pattern respond to its other inputs; nothing pins patterns.
  So the trigger fires *half*: path restriction as edge-vs-node is on par
  with the substitution value and belongs in D-006's frame; pattern
  freezing specifically is this project's own axis, inherited from Olsson
  et al., with no faithfulness-literature backing. Proposed as an O-011
  addendum.
- **Wang et al. freeze a different thing** — added 2026-09-19. Their
  [[path-patching]] holds every *non-sender head's output* at its clean
  value while MLPs and LayerNorms recompute [wang-2022 App. B]; this page's
  method holds every *attention pattern* and lets all outputs respond. A
  pattern-preserving ablation of `h` reaches later heads' values; path
  patching to the logits reaches nothing downstream except MLPs. So the
  path-restriction axis has at least three distinct points — total,
  pattern-frozen, other-heads-frozen — and the O-011 resolution's "direct
  effect" needs to say which freezing it means. Proposed as an O-011
  addendum.

## What this project does with it

- **E1 builds it — decided, O-011 resolution (2026-09-08).** Not as a boolean
  bolted onto D-006's substitution sweep, but as one **path-restriction**
  setting with three nesting values: total effect, pattern-preserving, direct
  effect. The third is what E4 needs as a baseline, which is why O-011 and the
  direct-effect half of O-007 were settled together. E3 ships four maps rather
  than six — D-006's three at total effect, plus the frozen-pattern variant for
  one substitution value, with the delta reported. A large delta escalates to
  the full cross; the R1 reading of Miller et al. can also reopen it. Wherever
  the axis is not swept, the setting is recorded next to the number.
- **E2 runs frozen.** Reproducing the induction-head ablation result means
  reproducing *this* ablation, and per epistemic rule 3 a number produced with
  unfrozen patterns is a different measurement rather than a noisier version of
  the same one. Stated limit for the E2 results doc: the paper publishes **no
  GPT-2 small ablation numbers** — its ablations are on its own small models —
  so E2 reproduces the method, not a number of theirs.
- **E4 provenance.** The masking caveat above is the earliest statement in this
  project's reading list of the effect E4 exists to decompose.
- **Epistemic rule 1 phrasing** for a result from this method: "under
  pattern-preserving zero-ablation on {dataset}, ablating head X changes
  {metric} by {amount}" — with "pattern-preserving" inside the method clause,
  not omitted from it.

## Sources

- [olsson-2022] Olsson et al., "In-context Learning and Induction Heads",
  Transformer Circuits Thread, 8 March 2022.
  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
  Sections cited: Argument 3 · Data Collection (2) Per-token losses (attention
  head ablations) · Ablation attribution to phase change.
- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: OV and QK Independence (The Freezing Attention Patterns
  Trick) · Term Importance Analysis.
- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 2.1 · App. B.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 3.1 (Table 1) · 3.1.2 · 4.1.

## Open questions

- **Does freezing patterns change the E3 heatmaps, and where?** Cheap to test
  once E1 exists; the answer determines whether this is a reported axis or a
  recorded default.
- **Is the frozen-pattern run itself off-distribution enough to matter?** It
  forces a state the model never produces. Nothing in Olsson et al. addresses
  the cost, and Miller et al. do not discuss the intervention at all. Open,
  and measurable at E3 via the O-011 delta.
- How does this interact with mean and resample substitution? The four
  combinations are all constructible and none are characterised here.
