---
title: Path expansion
type: method
status: drafted
sources: [elhage-2021, wang-2022]
first-needed: E1
updated: 2026-09-19
---

# Path expansion

## In one sentence

Write an attention-only transformer as a product of layers, **freeze the
attention patterns**, and multiply the product out into a **sum of end-to-end
paths** from tokens to logits — each path a chain of matrices that can be
inspected on its own and whose contribution can be measured by ablating it.

## Claim-licence block

| | |
|---|---|
| **Answers** | Decomposition: "with attention patterns held at their values on this input, which paths (direct, single-head, virtual-head) carry the logits, and what does each contribute?" With the term-importance ablation: the marginal loss reduction of all paths of a given order. |
| **Does NOT answer** | Anything about routing: freezing patterns removes the effect a head has on *where later heads look*, so Q- and K-composition are invisible in the logit expansion. Nothing about MLPs (the GeLU cannot be linearised through). Not necessity or sufficiency of any component on a distribution — paths are terms of an identity, not interventions, until the term-importance ablation is run. |
| **Confounds** | LayerNorm's per-token scalar is carried as a variable reweighting, so paths through different layers are not directly comparable. The expansion is exponential in depth. The frozen-pattern state is one the model never occupies naturally. Redundancy: a path can carry zero because another carries the same thing. |
| **Always log** | Which run supplied the frozen patterns; which terms were included (order cutoff); how LayerNorm was handled; seed and model revision hash. |

## Why it exists

A product of layers is opaque because every term is *a layer* — a bundle of
heads doing different things. A sum of paths is legible because every term is
*one route through the model*, and the paper's claim is that "each of these
end-to-end path terms is tractable to understand, can be reasoned about
independently, and additively combine to create model behavior" [elhage-2021
§The Path Expansion Trick]. This is the paper's central move; the QK/OV
circuits, skip-trigrams, virtual heads and the induction-head mechanism are all
things read off particular terms.

The method earns a page on this project because O-011's three
path-restriction values (total effect, pattern-preserving, direct effect) are
three ways of selecting terms from this expansion, and the E3 heatmaps will
be indexed by that choice.

## Intuition, then mechanism

**The analogy:** distributing a product over sums. $(a + b)(c + d)$ is opaque;
$ac + ad + bc + bd$ lists every way to pick one factor from each bracket. Here
each bracket is a layer, $(\mathrm{Id} + \sum_h A^h \otimes W_{OV}^h)$, whose terms are "do
nothing" (the identity, i.e. the residual connection) or "go through head $h$",
and a path is one choice per layer.

**Where the analogy breaks.** The attention patterns $A^h$ in the brackets
are not constants — they are computed from the very stream the earlier
brackets produced. The expansion is exact only after you freeze them. The
paper's thought experiment: run the model once and record every pattern; run
it again with the patterns forced to the recorded values. "This gives you a
function where the logits are a linear function of the tokens!" [elhage-2021
§OV and QK Independence (The Freezing Attention Patterns Trick)]. Everything
about *why* a pattern is what it is lives in a separate expansion, of the
attention scores, on [[attention-head-composition]].

**Now the mechanism.**

*Zero layers.* $T = W_U W_E$. The model can only map the present token to the
next, so the optimum is the bigram log-likelihood. This "direct path" term
appears in every deeper model and there still "can only affect the bigram
log-likelihoods"; in larger models it acts as a residual for bigram facts no
rule covers, e.g. `Barack → Obama` [elhage-2021 §Zero-Layer Transformers].

*One layer.*

$$
\begin{aligned}
T &= (\mathrm{Id} \otimes W_U) \cdot (\mathrm{Id} + \textstyle\sum_h A^h \otimes W_{OV}^h) \cdot (\mathrm{Id} \otimes W_E) \\
  &= \mathrm{Id} \otimes W_U W_E + \textstyle\sum_h A^h \otimes (W_U W_{OV}^h W_E)
\end{aligned}
$$

The direct path plus one term per head; the per-head term splits into the QK
and OV circuits on [[qk-ov-circuits]] [elhage-2021 §The Path Expansion Trick,
§Splitting Attention Head terms…].

*Two layers.* Expanding two brackets gives the direct path, the layer-1 head
terms, the layer-2 head terms, and cross terms $(A^{h_2} A^{h_1}) \otimes (W_U
W_{OV}^{h_2} W_{OV}^{h_1} W_E)$ — the **virtual attention heads** (V-composition)
[elhage-2021 §Path Expansion of Logits]. Depth $n$ gives terms of every order
up to $n$.

*With MLPs.* The pre-activations of an MLP in a one-layer model expand the same
way: $a_{\text{pre}} = W_I W_E + \sum_h A^h \otimes (W_I W_{OV}^h W_E)$, so "how much a token
excites this neuron directly" and "how much it excites it via head $h$" are
readable matrices. But the GeLU "means we can't linearize through MLP layers as
we did attention layers"; past it, the paper falls back to the Zoom In
programme of understanding individual neurons, and reports little success
[elhage-2021 §MLP Layers].

**One-line checkpoint:** freeze the patterns, distribute the product, and the
model is a sum of matrix chains — one per route — each of which you can read
and ablate.

## Precisely

**Term-importance ablation** — measuring the marginal effect of all $n$th-order
paths, without ever materialising the expansion [elhage-2021 §Term Importance
Analysis]:

1. Run the model; save all attention patterns.
2. Run again with every pattern forced to the saved values. Instead of adding
   each head's output to the stream, *save* it and add a zero tensor. Record
   the loss. (All paths through any head are now cut; only the direct path
   remains.)
3. Step $n$: run again with patterns frozen; for each head, save its output
   and replace it with the output saved for that head in the previous step.
   Record the loss. (Paths of order $\le n-1$ are now present.)

Differences between successive losses are the marginal contribution of the
$n$th-order terms. The paper notes that "freezing the attention patterns to
ground truth is what makes this ablation only target V-composition", and that
variants could isolate Q- or K-composition instead. In their two-layer model:
second-order (virtual-head) terms small; among first-order terms, layer-2
heads dominate layer-1 heads.

**LayerNorm.** Fold mean-subtraction, scale and bias into adjacent weights;
carry the per-token standard-deviation divisor as a scalar reweighting of every
path through that LayerNorm [elhage-2021 §Handling Layer Normalization]. First-
layer LayerNorm can alternatively be applied to every column of $W_E$ and then
ignored.

**Relation to Olsson et al.'s ablation.** Their pattern-preserving ablation is
step 2 applied to *one* head at a time with the others left intact; the
term-importance algorithm manipulates all heads at once and iterates over
order. Same freezing trick, different question. Recorded on
[[pattern-preserving-ablation]].

## What it licenses

- **Reading a term** licenses a claim about *weights along a route*: "the
  direct path from token $A$ through head $h$ to logit $C$ has this sign and
  size, with patterns fixed." Not a claim about behaviour on a distribution.
- **The term-importance ablation** licenses a *necessity-shaped* claim about
  an order of paths, at frozen patterns: "removing all paths of order $\ge n$
  changes loss by this much on this dataset." Because patterns are frozen, it
  is silent on Q/K-composition; the authors say so [elhage-2021 §Term
  Importance Analysis].
- **In attention-only models**, a pattern-preserving single-head ablation
  equals deleting that head's terms from the sum. Olsson et al. state that this
  equivalence "does not survive MLPs" — in GPT-2 small the identity is broken
  and the method is a heuristic [olsson-2022, via
  [[pattern-preserving-ablation]]].

## Where it's contested

- **Prior art.** The path structure "is not novel"; Dong et al. derived the
  same expansion studying expressivity. The paper's contribution is using it
  for mechanistic interpretability [elhage-2021 §Related Work: Mathematical
  Framework].
- **The expansion does not scale by itself.** Terms grow exponentially with
  depth; the paper's answer is the term-importance ablation (which never
  materialises the terms) and, empirically, that low-order terms dominate in
  small models. Whether that holds for GPT-2 small is unmeasured here.
- **"Fully understood" is a weak sense.** For one-layer models the expansion
  removes "algorithmic mystery" but leaves a table with billions of entries
  [elhage-2021 §Do We "Fully Understand" One-Layer Models?].

## What this project does with it

- **O-011's three settings, restated as term selection.** Total effect: ablate
  the head's write and let everything downstream, including patterns, respond
  — no expansion involved. Pattern-preserving: freeze patterns, remove the
  head's write — every term through the head is cut, Q/K-composition routes are
  held fixed. Direct effect: keep only the head's own term $A^h \otimes W_U W_{OV}^h
  (\ldots)$. The E1 design note should define the three this way, with this page as
  the reference. *Caveat added 2026-09-19:* that is **not** what Wang et al.
  measure as "direct effect". Their [[path-patching]] to the residual end
  state keeps every path from the head that avoids other *heads*, and MLPs
  and LayerNorms are recomputed along it [wang-2022 §3.1, App. B] — in a
  model with MLPs, that includes MLP-mediated terms this page's expansion
  cannot linearise. The two coincide only in attention-only models. E1 has
  to pick one and name it; proposed as an O-011 addendum.
- **E4's mechanical share** is the LayerNorm scalar this page folds out. The
  paper's remark that it "means that paths going through different sets of
  layers aren't easily comparable" is a warning for E4's decomposition, not
  only a bookkeeping note.
- **O-007.** The MLP expansion above is as far as the paper gets; the harness
  cannot borrow a linear story for MLPs from here.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Zero-Layer Transformers · The Path Expansion Trick ·
  Splitting Attention Head terms into Query-Key and Output-Value Circuits · OV
  and QK Independence (The Freezing Attention Patterns Trick) · Do We "Fully
  Understand" One-Layer Models? · Path Expansion of Logits · Term Importance
  Analysis · Related Work: Mathematical Framework · MLP Layers · Handling Layer
  Normalization.
- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 3.1 · App. B.

## Open questions

- Is the term-importance ablation worth running on GPT-2 small at E3 as a
  one-off, to learn whether virtual-head terms matter there? Cheap; would
  inform how much of E3's "indirect effect" is V-composition versus Q/K
  routing. Not scheduled.
