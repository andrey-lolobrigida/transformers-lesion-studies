---
key: wang-2022
title: "Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small"
authors: Wang, Variengien, Conmy, Shlegeris, Steinhardt
year: 2022
venue: arXiv preprint (v1, 1 November 2022); Redwood Research / UC Berkeley. Conference version [unverified from this copy]
arxiv: 2211.00593   # verified: printed on the arXiv HTML page header, "arXiv:2211.00593v1 [cs.LG] 01 Nov 2022"
url: https://arxiv.org/abs/2211.00593
local: papers/wang-2022-ioi/2211.00593.html
phase: R1
extraction: complete
feeds:
  - path-patching
  - activation-patching
  - mean-ablation
  - zero-ablation
  - circuit-validation-criteria
  - logit-difference
  - ioi-circuit
  - self-repair
  - circuit
  - induction-head
  - attention-head-composition
  - head-activation-evaluators
  - pattern-preserving-ablation
  - path-expansion
  - weight-statistics
---

# Source card — Wang et al. 2022

Read from the arXiv v1 HTML rendering (local copy). Five authors: four at
Redwood Research, Steinhardt at UC Berkeley. Code released as
`redwoodresearch/Easy-Transformer` (the paper's own pointer; whatever that
library later became is not stated in this source).

**Evidence base:** one model, **GPT-2 small** (12 layers × 12 heads), one
task family (IOI: 15 templates, 100 single-token names, 20 places, 20
objects, ABBA and BABA orders), one metric for interventions (IO−S logit
difference). Clean baseline over 100,000 samples; path patching averaged over
more than 200 pairs; the size of the mean-ablation reference set is not
stated. A preliminary look at GPT-2 medium is one paragraph of the
Discussion.

**Structural note:** Section 2 defines the task, the circuit-as-knockout
formalism and mean ablation on `p_ABC`. Section 3 discovers the circuit
backwards from the logits with path patching (3.1 Name Movers → 3.2
S-Inhibition → 3.3 Duplicate Token, Induction, Previous Token → 3.4 Backup
Name Movers). Section 4 validates it with faithfulness, completeness and
minimality against a naïve baseline, then builds adversarial examples.
Thirteen appendices carry the algorithms, templates, the random-token
validations, the MLP experiment and the minimality sets.

## Structure

| Section | What it holds |
|---|---|
| 1 Introduction | Three "insights": redundancy incl. backup heads; known structures used unexpectedly; negative heads |
| 2 Background, 2.1 Circuits and Knockouts | Task, metrics, notation; circuit as subgraph with $C(x)$ via knockout; zero vs mean ablation; `p_ABC`; template-matched means |
| 3 Discovering the Circuit | The three-step algorithm; seven head classes; MLPs not intervened on |
| 3.1–3.4 | Path patching per receiver; head characterisation; token/position signals; the Backup Name Mover discovery |
| 4 Experimental validation | $F(C)$; faithfulness 87%; completeness (three searches); minimality; naïve baseline; adversarial examples |
| 5 Discussion | Pointers; compensation; negative heads beyond IOI; limitations (S-Inhibition attention, MLPs, LayerNorm); GPT-2 medium |
| App. A | Six counterfactual datasets; $2.31\, S_{\text{pos}} + 0.99\, S_{\text{tok}}$; relative-position check |
| App. B | Path patching, Algorithm 1, four forward passes; freezing defined |
| App. C, D | S-Inhibition keys (fuzzy heads); Previous Token heads via Induction keys; Q-composition route null |
| App. E, L | Templates; adversarial sentences |
| App. F | Backup Name Movers in detail; "reason and mechanism still unclear" |
| App. G | GPT-2 small architecture, LayerNorm definition, Algorithm 2 |
| App. H, I | Random-token validations: previous-token, induction, duplicate scores; copy check |
| App. J | MLP knockouts and direct effects |
| App. K, M | Minimality sets; greedy completeness search, Algorithm 3 |

## Extraction log

**2026-09-19 — complete.**

Read in full from the local HTML copy, main text and all appendices. Opened
six method pages (path patching; activation patching; mean ablation; zero
ablation as a stub; circuit validation criteria; logit difference) and two
concept pages (the IOI circuit; self-repair as a phenomenon). Edited
[[circuit]] (behavioural definition, reconciliation proposal for D-010),
[[induction-head]] (IOI role; GPT-2 small indices; O-012 evidence),
[[attention-head-composition]] (all three kinds observed behaviourally),
[[head-activation-evaluators]] (Wang's variants and rankings),
[[pattern-preserving-ablation]] and [[path-expansion]] (the direct-effect
definition conflict), [[weight-statistics]] (copy score cross-reference).
Terms proposed for `docs/05-glossary.md`. Addenda proposed to O-003, O-007,
O-011, O-012; one new open question proposed (O-013, unit of ablation).

**Deliberately left:**

- **The head-by-head characterisation figures** (attention-vs-projection
  scatters, attention patterns on sample sequences). The claims they support
  are recorded with the figure number; the plots themselves are for the
  reader.
- **Appendix G's architecture restatement.** Standard GPT-2; nothing there
  differs from [[residual-stream]] / [[attention-head]].
- **The related-work framing** (causal mediation analysis, Vig et al.;
  causal abstraction, Geiger et al.). R1 skim or R3.
- **The safety motivation in the introduction.** Not this project's claim.
- **The GPT-2 medium paragraph** beyond one line on [[ioi-circuit]].

**Recorded source inconsistencies** (flagged on the pages, not resolved):

1. The clean logit difference is 3.56 in §2 and §4 (100,000 samples), 3.55
   in Fig. 8 and App. A's baseline, 3.56 in App. A's prefix-length control.
   Sample sizes differ and are not reconciled.
2. The Duplicate Token heads are identified in §3.3 without indices; the
   indices (0.1, 3.0) appear in App. C and App. I. Minor.

**Not resolvable from this source, carried on the pages:** the reference-set
size behind every mean; the cause of the backup effect (dropout is a stated
conjecture); what the S-Inhibition heads' attention is computed from; how
the Induction heads produce a position signal; the MLPs' role beyond
Appendix J; whether any of the numbers survive a change of knockout method.

## Note on citing

Numbered sections and lettered appendices. Wiki citations: `[wang-2022 §3.1]`,
`[wang-2022 App. B]`, footnotes as `fn. n`, figures as `Fig. n`, algorithms
by number. The arXiv ID is verified from the page itself; the conference
venue is not stated in the v1 text and is left unverified.
