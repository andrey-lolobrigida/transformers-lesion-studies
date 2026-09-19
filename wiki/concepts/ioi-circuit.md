---
title: IOI circuit (indirect object identification in GPT-2 small)
type: concept
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E1
updated: 2026-09-19
---

# The IOI circuit

*This page is about an object — the set of heads Wang et al. identified and
the numbers attached to them — because E1's battery and E2's reproduction
target it. It is not a summary of the paper; the methods are on their own
pages and the argument structure is on the source card.*

## In one sentence

Twenty-six (head, position) nodes in GPT-2 small, grouped into seven classes,
which under path patching and mean ablation on `p_ABC` account for 87% of
the model's IO−S logit difference on the IOI task — by detecting which name
is duplicated, inhibiting attention to it, and copying the other name.

## Why it exists

The task: "When Mary and John went to the store, John gave a drink to" →
"Mary". The first clause introduces the indirect object (IO) and the subject
(S); the main clause repeats S; the task is to predict IO. S1 and S2 are the
two occurrences of S; END is the final position [wang-2022 §2]. It was
chosen because it "admits an interpretable algorithm: of the two names in
the sentence, predict the name that isn't the subject of the last clause"
[wang-2022 §1].

The page exists because the roadmap lists IOI as the battery item with
"published numbers to check against", and this is where those numbers are
gathered with their conditions attached.

## Intuition, then mechanism

**The algorithm the authors claim the model implements** [wang-2022 §3]:

1. Identify all previous names in the sentence.
2. Remove the duplicated one.
3. Output the remaining name.

**Where the analogy to a program breaks.** Steps are not executed by one
component each. Each step has *several* heads doing overlapping work, there
is a class of heads pushing *against* the answer, and there is a class that
does nothing measurable until the main copying heads are removed. And the
"removal" in step 2 is not a deletion: it is a signal that makes later heads
*attend elsewhere*.

**Mechanism, by class** [wang-2022 §3, §3.1–3.4, App. C, App. D, App. F]:

| Class | Heads | Active at | Attends to | Does |
|---|---|---|---|---|
| Duplicate Token | 0.1, 3.0 (fuzzy: 0.10) | S2 | S1 | Signals duplication; writes the *position* of the earlier occurrence |
| Previous Token | 2.2, 4.11 | S1+1 | S1 | Copies S into the position after S1 |
| Induction | 5.5, 6.9 (fuzzy: 5.8, 5.9) | S2 | S1+1 | Same role as Duplicate Token heads, via the induction mechanism (K-composition with the Previous Token heads) |
| S-Inhibition | 7.3, 7.9, 8.6, 8.10 | END | S2 (mean 0.51) | Writes into Name Movers' *queries* a token signal and a position signal that make them avoid S1 and S2 |
| Name Mover | 9.6, 9.9, 10.0 | END | IO (mean 0.59) | Copies the attended name to the logits; copy score > 95% vs < 20% for an average head |
| Negative Name Mover | 10.7, 11.10 | END | names | Writes *against* the attended name; negative copy score 98% vs 12% |
| Backup Name Mover | 9.0, 9.7, 10.1, 10.2, 10.6, 10.10, 11.2, 11.9 | END | varies | Little direct effect intact; become the main direct contributors when the Name Movers are knocked out |

Notation `layer.head`. Classes were found by tracing back from the logits
with [[path-patching]]; each class was then characterised by attention
patterns and targeted tests [wang-2022 §3].

**Two signals in the S-Inhibition output.** A *token* signal (the identity
of S) and a *position* signal (where S1 is). Both matter; position matters
more: patched logit difference ≈ `2.31 S_pos + 0.99 S_tok` [wang-2022 §3.2,
App. A]. The position signal originates in the Duplicate Token and Induction
heads and is passed by V-composition into the S-Inhibition heads: patching
those heads' outputs from altered-position sentences reproduces ≥ 88% of the
S-Inhibition effect; altered names at the same positions, < 8% [wang-2022
§3.3]. It appears to be a *relative* position (S1 to S2): lengthening the
prefix at constant S1–S2 distance leaves the logit difference at 3.56 → 3.57
[wang-2022 §App. A]. The authors call this heads "communicating by using
pointers (sharing the location of a piece of information instead of copying
it)" [wang-2022 §5].

**Induction heads here do not do induction.** Their output "is used both as
a pointer to S1 and as a signal that S is duplicated" [wang-2022 §3]; "in the
context we study, Induction Heads perform a different function compared to
what was described in their original discovery … We did not investigate how
this mechanism was implemented" [wang-2022 §3.3]. They still pass Olsson et
al.'s prefix-matching and copying tests on repeated random tokens
[wang-2022 §App. H]; see [[induction-head]].

**Negative heads.** Speculated to "help the model 'hedge' so as to avoid high
cross-entropy loss when making mistakes" [wang-2022 §3]. On repeated random
sequences they, and most Name Movers and Backups, write in the next-token
direction — the Negative ones negatively — "suggest[ing] that these heads
are involved beyond the IOI task" [wang-2022 §App. H].

**One-line checkpoint:** early heads mark the duplicate's position, middle
heads turn that into "don't look there", late heads copy whatever is left —
with spares and a brake.

## Precisely

**Datasets** [wang-2022 §2, App. E, App. L]: 15 templates (all in the BABA
pattern, ABBA obtained by swapping the first two names), 100 single-token
first names, hand-made lists of 20 places and 20 objects. `p_IOI` is the
resulting distribution. `p_ABC` uses the same templates with three unrelated
random names. Adversarial sets add a natural sentence containing IO (or,
as control, S) between the clauses.

**Numbers to check against.** Every one is under the paper's own conditions:
knockouts are [[mean-ablation]] on `p_ABC`, template-matched, per (head,
position); path patching corrupts from `p_ABC`; metric is [[logit-difference]].

| Quantity | Value | Conditions | Where |
|---|---|---|---|
| Clean mean logit difference | 3.56 | 100,000 samples | §2 |
| Clean IO probability; IO over S | 49%; 99.3% | same | §2 |
| Name Movers' mean attention to IO | 0.59 | `p_IOI` | §3.1 |
| Name Mover attention-vs-projection correlation | ρ > 0.81 | N = 500 | §3.1 |
| Name Mover copy score / average head | > 95% / < 20% | N = 1000, top-5 | §3.1 |
| Negative Name Mover negative copy score / average | 98% / 12% | same | §3.1 |
| S-Inhibition mean attention END → S2 | 0.51 | four heads | §3.2 |
| Position vs token signal weights | 2.31 vs 0.99 | six datasets, 7% mean error | App. A |
| Faithfulness `|F(M) − F(C)|` | 0.46 (13%); C at 87% | 26 nodes | §4 |
| Drop after knocking out the three Name Movers | ≈ 5% | mean ablation | §3.4, App. F |
| Greedy incompleteness, max | 3.09 (87%) | k = 10, 10 runs | §4.1 |
| Minimality, every node | ≥ 1% of `F(M)` | per-node `K` in App. K | §4.2 |
| Naïve circuit faithfulness | 0.1 | see §4.3 | §4.3 |
| Adversarial (duplicate IO): logit diff; S over IO | 1.23; 23.4% | App. L templates | §4.4 |
| Control (extra S) | 3.64; 0.4% | | §4.4 |
| MLP0 knocked out | sign reverses | mean ablation | App. J |
| All MLPs but MLP0 knocked out | −1.1 | | App. J |
| Path-patching averages | > 200 pairs | | App. B |

Not given: the reference-set size for the means; per-head scores on the
random-token evaluators (only rankings — 4.11 and 2.2 top two on previous
token; 5.5 and 6.9 in the top five on induction and top twenty on copying;
3.0 and 0.1 in the top three on duplicate) [wang-2022 App. H, App. I].

**Copy score** [wang-2022 §3.1]: take the residual stream at a name token
after MLP0, multiply by the head's OV matrix, then by `W_U`, apply the final
LayerNorm, and count the proportion of samples with the name in the top five
logits. The *negative* copy score uses `−W_OV`. A hybrid of a weight
statistic and an activation: the input is a real residual vector, not `W_E`.
Compare [[weight-statistics]] and [[head-activation-evaluators]].

## What it licenses

The circuit is a claim of the form: "under path patching from `p_ABC` and
mean ablation on `p_ABC`, these 26 nodes are necessary along these routes,
and with everything else knocked out they retain 87% of the logit
difference." It is validated by [[circuit-validation-criteria]] and *fails*
the strongest of them (greedy completeness) — the authors say so.

It does **not** license "these heads are the IOI mechanism" in a
knockout-independent sense; [[circuit]] on why. It does not license a
description of what the S-Inhibition heads' *attention* is computed from
(the authors list this as not understood [wang-2022 §5]), nor of how the
Induction heads produce a position signal, nor of the MLPs' role.

## Where it's contested

- **Missing validations, listed by the authors** [wang-2022 §3.3]: for
  Duplicate Token heads, whether the QK matrix acts as a collision detector
  and the OV copies positional embeddings; for Induction heads, the
  Elhage-style parameter analysis. "Omitted due to time constraints."
- **Backup head membership is partly arbitrary**: eight heads above a 2%
  threshold not already in a class; "the exact choice of Backup Name Mover
  Heads doesn't change significantly the behavior of the circuit"
  [wang-2022 §App. F].
- **Greedy incompleteness at 87%** — the circuit is not complete, and the
  missing sets mix classes [wang-2022 §4.1].
- **The adversarial set exposes behaviour outside the analysis**: S-Inhibition
  heads attend to the second IO, a pattern absent from both `p_IOI` and
  `p_ABC` [wang-2022 §4.4].
- **The 87% is one point in a six-tuple space** — Miller et al., added
  2026-09-19. The circuit is specified as edges and positions but was
  evaluated node-wise; evaluated as specified (edge level, specific
  positions) its median logit difference recovered is "well over 100%".
  Resample instead of mean lowers it; all positions instead of the
  circuit's lowers it; BABA scores above ABBA; the score rises with the
  size of the ABC mean set, which Wang et al. put at about seven per
  template; per-prompt scores have an interquartile range up to 50 points
  [miller-2024 §4, §4.1, §4.2]. Every entry in the numbers table above is
  under Wang et al.'s six-tuple only. Detail on
  [[circuit-validation-criteria]] and [[ablation-methodology]].
- **GPT-2 medium** has "a sparse set of heads directly influencing the
  logits. However, not all of these heads attend to IO and S" — a preliminary
  observation that the structure does not transfer as-is [wang-2022 §5].
- **Redundancy is expected on sub-distributions**, by the authors' own
  footnote: "it is unlikely that SGD would select for perfectly redundant
  modules, but redundancy is more likely when analyzing a sub-distribution
  of all of a model's training data or a subtask of its behavior"
  [wang-2022 §3.4, fn. 2].

## What this project does with it

- **E1's IOI battery item**: `p_IOI` and `p_ABC` generators as specified
  above, single-token vocabularies, ABBA and BABA, metric IO−S, expected
  direction "down" except for the two Negative heads. The adversarial
  templates are a cheap extra item with a published number.
- **E2 reproduces**: the clean baseline (3.56), the three path-patching
  rows on [[path-patching]] (head identities and signs), the Name Mover
  knockout (≈ 5% drop) and the faithfulness figure (87%) — each with the
  knockout conditions matched or the mismatch stated. O-013 asks whether the
  harness can match the (head, position) unit at all.
- **E3**: the two Negative heads are the known sign-flip case for the
  heatmaps; the Backups are the known case of a head whose single-ablation
  effect understates it.
- **E4**: the Backup Name Movers are the originating observation; see
  [[self-repair]].
- **O-012**: the K-composition route (Previous Token → Induction keys) is
  found on IOI; the Q-composition route is not [wang-2022 App. D]. Evidence,
  not resolution — see the O-012 addendum.

## Sources

- [wang-2022] Wang, Variengien, Conmy, Shlegeris & Steinhardt,
  "Interpretability in the Wild: a Circuit for Indirect Object Identification
  in GPT-2 small", arXiv 2211.00593v1, 1 November 2022.
  https://arxiv.org/abs/2211.00593
  Sections cited: 1 · 2 · 3 · 3.1 · 3.2 · 3.3 · 3.4 (fn. 2) · 4 · 4.1 · 4.2 ·
  4.3 · 4.4 · 5 · App. A · App. B · App. C · App. D · App. E · App. F ·
  App. H · App. I · App. J · App. K · App. L.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 4 · 4.1 · 4.2.

## Open questions

- Which of the numbers above are reproducible with *whole-head* ablation,
  and which require the (head, position) unit? (O-013.)
- The S-Inhibition attention pattern and the MLPs are the two unexplained
  parts the authors name. Neither is on this project's path unless O-007
  makes MLPs first-class.
