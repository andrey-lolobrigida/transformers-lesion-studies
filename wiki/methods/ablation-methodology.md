---
title: Ablation methodology (the six-tuple)
type: method
status: drafted
sources: [miller-2024, wang-2022, meng-2022]
first-needed: E1
updated: 2026-09-20
---

# Ablation methodology — the six-tuple

## In one sentence

An ablation experiment on a transformer circuit is specified by **six
choices** — graph granularity, component type, ablation value, token
positions, direction, and which set is ablated — and Miller et al. show that
the faithfulness score of a fixed circuit moves with each of them, so a
number reported without all six is not a measurement of the circuit.

## Claim-licence block

| | |
|---|---|
| **Answers** | "Under *this* six-tuple and *this* metric, how does the model's output change?" It is the frame every other method page on this wiki sits inside: [[zero-ablation]], [[mean-ablation]], [[resample-ablation]] are values of one axis; [[path-patching]] is one setting of another. |
| **Does NOT answer** | Which six-tuple is *correct*. The paper's thesis is that there often is no correct one: "the optimal circuit with respect to only a set of prompts is undefined. The ablation partly determines the task" [miller-2024 §5]. Two constraints only: a circuit specified as edges is tested with edge ablation; one specified with token positions is tested position-specifically [miller-2024 §5, §6]. |
| **Confounds** | Every axis is a confound for every other when unstated. The prior literature's seven methodologies "each … differs from all of the others in at least one aspect" [miller-2024 Table 2]. The metric is a seventh, free choice [miller-2024 §3.2]. |
| **Always log** | All six, plus the metric, the mean-ablation set size, the clean and corrupt distributions, and the averaging order of the metric. Rule 4 and the O-011 "record the default" rule are both instances of this row. |

## Why it exists

The faithfulness of a circuit — how much of the model's performance survives
when everything outside it is ablated — had become the standard number for
saying a circuit is real. Miller et al. ask "What do circuit faithfulness
metrics actually show? To what extent are they a useful test of the circuit
and to what extent are they a reflection of the experimental methodology?"
[miller-2024 §1]. Their answer: existing scores "reflect both the
methodological choices of researchers as well as the actual components of
the circuit" [miller-2024 Abstract].

This page is the source for epistemic rule 3 ("the ablation defines the
task") and for D-006. It earns its place because E1's harness is, in effect,
an implementation of this table, and E3's "four maps" are four points in it.

## Intuition, then mechanism

**The analogy:** a lab protocol. "We measured the enzyme's activity" means
nothing without temperature, pH, substrate concentration and the assay. Two
labs at different pH get different numbers for the same enzyme and neither is
wrong; the protocol is part of the quantity.

**Where it breaks.** With an enzyme there is a fact about which conditions
are physiological. Here the paper's claim is stronger: in a *compiled*
model with a known program, the "ground-truth circuit" itself differs
between two ablation values, because one of them removes information the
other leaves in place [miller-2024 §5]. There is no physiological pH to
appeal to; the choice is about which task you mean.

**Now the mechanism.** An ablation is a $\operatorname{do}$ intervention on activations
outside the circuit:

$$
F(x) = M(x \mid \operatorname{do}(a = \tilde a)), \quad a \notin C
$$

with $a$ an internal activation and $\tilde a$ its ablated value [miller-2024
§3.1, eq. 1]. The six choices [miller-2024 §3.1, Table 1]:

| # | Axis | Values seen in the literature | This project's handle |
|---|---|---|---|
| 1 | **Granularity** | heads and MLPs (most common; Q/K/V inputs separately); layers (ROME); neurons (Vig); subspaces; sparse features | D-003; O-007 |
| 2 | **Component type** | node; edge (factorised view); branch (treeified view; causal scrubbing) | O-011, reframed — see below |
| 3 | **Value** | zero; Gaussian noise (ROME); resample (a.k.a. activation patching); mean (with a set-size sub-choice) | D-006 |
| 4 | **Token positions** | all; only positions not in the circuit's specified set | O-013 |
| 5 | **Direction** | ablate clean (clean input, corrupt values in); restore clean (corrupt input, clean values in) | rule 2 |
| 6 | **Set** | the circuit; its complement | E3 ablates single components, which is neither |

**Component type** rests on three equivalent views of the model
[miller-2024 §3.1.2, App. B]: the *residual* view (every component reads
the stream); the *factorised* view (every component has an edge to every
earlier one — Elhage et al.'s virtual weights, [[residual-stream]]); the
*treeified* view (every input-to-output path separated). Node ablation
replaces a component's output and "all downstream nodes 'see' the change".
Edge ablation replaces what *one* destination receives from *one* source.
Branch ablation acts on a whole input-to-output path; it is the primitive of
causal scrubbing and is exponential in depth, so the paper omits it.

**Direction × set** gives four experiments with four different targets
[miller-2024 §3.1.5, Table 3]:

| Input | Direction | Set | What faithfulness means |
|---|---|---|---|
| Clean | ablate clean | circuit | destroy performance |
| Corrupt | restore clean | circuit | restore performance |
| Clean | ablate clean | complement | maintain performance |
| Corrupt | restore clean | complement | maintain inefficacy |

The two "maintain" rows both compare to the full model but are not
equivalent: restoring clean values into the circuit on a corrupt input
"allows the signal from the clean input to flow through edges not included
in the circuit", whereas ablating the complement on a clean input "ensures
that the signal from the input only flows through the circuit"
[miller-2024 §3.1.5, Fig. 2].

**One-line checkpoint:** six dials plus a metric; the same circuit reads
differently at every setting; the settings are the experiment.

## Precisely

**Where the prior work sits** [miller-2024 Table 2], for the two sources
this wiki has read and the two it will:

| Work | Granularity | Component | Value | Positions | Direction | Set |
|---|---|---|---|---|---|---|
| Wang et al. (IOI) | heads | node (evaluation) / path (discovery) | mean | specific | ablate clean | complement |
| Meng et al. (ROME) | layers | node | resample (clean) | specific | resample clean | circuit |
| Vig et al. | heads, neurons | node | resample (clean) | all | resample clean | circuit |
| Conmy et al. (ACDC) | heads, MLPs | edge | resample (corrupt) | all | ablate clean | complement |

*ROME row, checked against the source (skim, 2026-09-20).* The
"layers" granularity is two things: single hidden states $h_i^{(l)}$ for the
main map, and **windows of ten consecutive layers** of MLP or attention
outputs for the module maps, because single-module restoration was
"generally negligible" [meng-2022 App. B.2]. The Gaussian noise that Table
1 lists as an ablation *value* is, in ROME, the corruption applied to the
subject-token embeddings (at three times the embedding std); the
intervention on the mediator is resample-clean [meng-2022 §2.1, App. B.1].
Both readings fit eq. 1 — the noise ablates the embedding nodes, the
restore patches the mediator — but E1 records them as *corrupt
distribution* and *value* respectively. Page: [[causal-tracing]].

**What Miller et al. measured on the IOI circuit**, varying one axis at a
time from Wang et al.'s setting (node · mean · specific positions ·
ablate clean · complement; logit difference recovered) [miller-2024 §4.1,
Figs. 3, 4]:

- *Component:* edge ablation "returns substantially higher percentages";
  the edge-level circuit at specific positions "has a median score well
  over 100%, as this best represents the hypothesis of Wang et al."
- *Value:* resample from ABC is "systematically lower" than mean
  (t-test p = 1e−5 for node ablation; not significant for edge). Their mean
  is over 100 ABC prompts; Wang et al.'s used "around seven examples per
  template".
- *Positions:* ablating all positions "consistently results in lower
  faithfulness scores".
- *Clean distribution:* BABA prompts score systematically higher than ABBA.
- *Mean set size:* faithfulness "monotonically increases with the size of
  the ABC dataset". No mechanism is offered.
- *Averaging order:* Wang et al. compute the ratio of mean logit
  differences; the mean of per-prompt ratios "return[s] substantially
  higher percentages".
- *Per-prompt spread:* interquartile range up to 50 points; outliers "in
  the tens of thousands of percent"; "while the circuit matches the
  behavior on average, it does not match it for many examples"
  [miller-2024 §4.2].

Exact values are read off figures, not tabulated in the text; the one
number quoted is Wang et al.'s original 87%.

**Two further circuits** [miller-2024 App. D]: the Docstring circuit
(4-layer attention-only model) scores much higher under edge-mean than
edge-resample, and much lower once positions are respected — "the circuit
is in fact performing significant computation on token positions outside
the circuit". The Sports Players circuit (Pythia 2.8B) shows a "dramatic
difference" between resample and mean on accuracy, explained by the corrupt
prompt always naming a different sport, so resample "adds signal"; the
authors note this does not negate the original hypothesis, which was about
localisation rather than a full circuit.

**The compiled-model result** [miller-2024 §5, App. D.3]: in the Tracr
X-Proportion model the edge from Input to Attn 1.0 carries only positional
encoding, constant across inputs. Under resample ablation it is not needed;
under zero ablation it is. Conmy et al. took the zero-ablation edges as
ground truth and their resample-based algorithms "fail"; with the
resample-ablation edges as ground truth "all three algorithms perfectly
recover" it.

## What it licenses

- The six-tuple licenses a *complete statement* of an ablation result. Rule
  1's template gains its missing slots: "under {value} {component}
  ablation of {set} at {positions}, {direction}, at {granularity}, on
  {distribution}, metric {m}, …".
- The IOI results license: "the faithfulness score of the IOI circuit is
  not a property of the circuit alone." They do **not** license "the IOI
  circuit is wrong" — the authors are explicit that a different
  methodology "may have led them to include different edges", not that the
  edges found are false.
- The Tracr result licenses the strong form of rule 3: two ablation values
  define two different correct circuits for one program. "Do you want your
  IOI circuit to include the mechanism that decides it needs to output a
  name? Then use zero ablations. Or do you want to find the circuit that,
  given the context of outputting a name, completes the IOI task? Then use
  mean ablations" [miller-2024 §6].

## Where it's contested

- **Attention-pattern freezing is not one of the six.** Olsson et al.'s
  [[pattern-preserving-ablation]] pins patterns; nothing in the six-tuple
  names that intervention. The nearest axis is component type: an edge
  ablation restricts which *destination* sees the change, in the factorised
  view, which is a path restriction of a different kind. So the O-011
  question "does the faithfulness literature treat path restriction as a
  first-class choice?" gets a split answer: *edge vs node*, yes, first-class
  and empirically consequential; *pattern freezing*, absent. Proposed as an
  O-011 addendum.
- **Direct effect is edge-level in this vocabulary.** Wang et al.'s path
  patching "is equivalent to Edge Resample Ablation in our terminology",
  with "MLPs considered to be part of the direct path between nodes"
  [miller-2024 App. F]. That confirms the discrepancy recorded on
  [[path-patching]] and gives it a name: Wang's direct effect is an edge
  ablation in a graph whose nodes are heads only.
- **Activation patching is a value, not a method, here.** The paper uses
  "activation patching" and "resample ablation" interchangeably and treats
  node patching with a cached activation as "vanilla activation patching"
  [miller-2024 §3.1, §3.1.2]. The glossary's "activation patching tests
  sufficiency" is, in this frame, a statement about axis 5, not about the
  method.
- **Single-component ablation is off the table's "set" axis.** E3 ablates
  one head at a time, which is neither the circuit nor the complement. The
  paper's sensitivity results are for whole-complement ablations of a fixed
  circuit; how much transfers to single-head effect sizes is not measured
  here.
- **Zhang & Nanda 2024** studied a subset of the same choices and, per
  Miller et al., prescribe best practices, where Miller et al. decline to
  ("rather than prescribing a single correct approach") [miller-2024 §2].
  Not on the reading list; recorded.

## What this project does with it

- **E1's harness config is this table.** Every run artifact records all
  six axes plus metric, set size and averaging order. "Default" is a
  value, never an omission.
- **E3's maps** are axis 3 (three values) × one of axis 2's settings, at
  granularity = heads, positions = all, direction = ablate clean, set = one
  component. The O-011 delta test is a comparison on axis 2 (or on the
  pattern-freezing intervention the table does not name — the addendum
  decides which).
- **E2** reproduces Wang et al. at Wang et al.'s six-tuple (node · mean ·
  specific positions · complement), then reports Miller et al.'s
  one-axis-at-a-time variations as the adversarial check rule 7 requires.
  Both published figures exist: 87%, and "median well over 100%" at edge
  level.
- **Metric hygiene**: report `[mean logit diff] %` *and* `mean [logit diff
  %]`, and the per-prompt interquartile range, not a single ratio.
- **`auto-circuit`** implements edge patching with mean, zero and
  resample on TransformerLens models [miller-2024 App. A]. Whether E1
  builds on it or reimplements is an E0 decision; it is the reference
  implementation of axis 2's edge setting either way.

## Sources

- [miller-2024] Miller, Chughtai & Saunders, "Transformer Circuit
  Faithfulness Metrics Are Not Robust", arXiv 2407.08734v1, 11 July 2024.
  https://arxiv.org/abs/2407.08734
  Sections cited: Abstract · 1 · 2 · 3.1 (eq. 1, Tables 1, 2) · 3.1.2 ·
  3.1.3 · 3.1.4 · 3.1.5 (Table 3, Fig. 2) · 3.2 · 4.1 (Figs. 3, 4) · 4.2 ·
  5 · 6 · App. A · App. B · App. D · App. D.3 · App. F.
- [wang-2022] Wang et al., 2022 — the methodology Miller et al. vary; §2.1,
  §4.

## Open questions

- Does the six-tuple sensitivity carry over to **single-head effect sizes**
  (E3's object) or only to whole-complement faithfulness? Nothing here
  measures it; E3 can, for free, by running the O-011 delta.
- Where does pattern freezing go in the table — a seventh axis, or a
  variant of axis 2? Proposed for the E1 design note.
