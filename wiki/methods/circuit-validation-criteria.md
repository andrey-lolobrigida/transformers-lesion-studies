---
title: Circuit validation criteria (faithfulness, completeness, minimality)
type: method
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E2
updated: 2026-09-19
---

# Circuit validation criteria

## In one sentence

Three knockout-based scores for a proposed circuit $C$ inside a model $M$:
**faithfulness** (does $C$ alone perform like $M$?), **completeness** (does
$C$ keep performing like $M$ when the *same* pieces are removed from both?),
and **minimality** (does every node in $C$ earn its place under *some*
knockout?).

## Claim-licence block

| | |
|---|---|
| **Answers** | Faithfulness: "with everything outside $C$ knocked out, how much of the metric survives?" Completeness: "is there a subset $K \subseteq C$ whose removal hurts $C$ much more than it hurts $M$?" — i.e. does $M$ have something outside $C$ that fills in. Minimality: "for node $v$, is there a context $K$ in which removing $v$ matters?" |
| **Does NOT answer** | Whether $C$ is *the* mechanism. Faithfulness is explicitly not enough: the paper's toy example (two identical parallel circuits behind an OR) is faithful with either half alone. None of the three is a sufficiency claim in rule 2's sense; all are computed by knocking things out. Completeness is only ever *searched*, never proven — the subset space is exponential. |
| **Confounds** | Every score is an $F$ computed under one knockout method on one reference distribution ([[mean-ablation]] on `p_ABC`, per (head, position)); change the knockout and the numbers change. Completeness depends on the search strategy: random and class-wise $K$ said "complete", greedy $K$ said otherwise. Minimality's $K$ is chosen per node by hand. |
| **Always log** | Knockout method and reference; the metric $f$; the exact $C$; for completeness, the sampling strategy and every $K$ tried; for minimality, the $K$ used per node; sample sizes; seed; model revision hash. |

## Why it exists

Section 3.4 of the paper had already shown that a circuit can look complete
and not be: knocking out the three Name Movers cost only about 5% of the
logit difference because other heads took over. So "we therefore seek more
systematic validations to check that our account … includes all components
used by the model" [wang-2022 §4]. The three criteria are the paper's answer,
and the abstract describes them as *supporting* the explanation while
*pointing to remaining gaps* — both halves are results.

The page exists because Miller et al. (R1) is titled "Transformer Circuit
Faithfulness Metrics are not Robust", and `docs/01-methods.md` already
paraphrases their conclusion. This page records what the metric *is*, from
its source, so that the robustness claim has a definite object.

## Intuition, then mechanism

**The analogy:** checking a parts list for a machine. *Faithfulness*: build
the machine from the listed parts only — does it run? *Completeness*: take
the same part out of the listed build and the real machine — do they fail
the same way? If the real machine keeps running, it had a spare you did not
list. *Minimality*: for each listed part, is there some configuration in
which removing it matters? If not, it was padding.

**Where it breaks.** The machine analogy assumes parts either work or do not.
Here "run" is a continuous metric, and "remove" means mean-ablate on a
reference distribution, so every criterion is a number relative to a
knockout choice — there is no knockout-free fact of the matter. And the
completeness check has to *search* for the spare; not finding one under one
search says less than it seems.

**Mechanism.** Let $f(C(X); X)$ be the IO−S logit difference when the circuit
$C$ runs on input $X$ — $C(X)$ meaning $M$ with every node outside $C$
knocked out — and $F(C) = \mathbb{E}_{X \sim p_{\text{IOI}}}[f(C(X); X)]$ [wang-2022 §4].

- **Faithfulness:** $\lvert F(M) - F(C) \rvert$ small. Result: 0.46, which is 13% of
  $F(M)$ = 3.56; "C achieves 87% of the performance of M" [wang-2022 §4].
- **Completeness:** for every $K \subseteq C$, the *incompleteness score*
  $\lvert F(C \setminus K) - F(M \setminus K) \rvert$ should be small. "C and M should not just be
  similar, but remain similar under knockouts" [wang-2022 §4.1]. Searched
  three ways: $K$ uniformly random; $K$ = one whole class of heads; $K$
  built greedily, node by node, to maximise the score (Algorithm 3, App. M:
  sample $k$ candidate nodes, add the one that moves the score most, repeat;
  $k$ = 10 for the full circuit and 5 for the naïve one; 10 runs, 5 best
  sets kept). The first two methods found only small scores; the greedy one
  found scores **up to 3.09 — 87% of the original logit difference** — with
  sets "usually not semantically interpretable (containing heads from
  multiple categories)" [wang-2022 §4.1, App. M, Fig. 22].
- **Minimality:** for every $v \in C$ there should exist $K \subseteq C \setminus \{v\}$ with a
  large *minimality score* $\lvert F(C \setminus (K \cup \{v\})) - F(C \setminus K) \rvert$ [wang-2022 §4.2].
  For most heads, $K$ = the rest of $v$'s class works; some need a hand-picked
  $K$ (the Induction heads 5.9 and 5.8 are scored against $K$ = the two
  Negative Name Movers, for instance). All 26 nodes score at least 1% of
  $F(M)$; the Backup Name Movers are the smallest [wang-2022 §4.2, App. K,
  Fig. 20].
- **Baseline:** a *naïve* circuit — Name Movers, S-Inhibition, two Induction,
  two Duplicate Token, Previous Token heads; no Backup or Negative heads —
  has faithfulness 0.1, "comparable to the full circuit", but is *more easily*
  shown incomplete by random and class-wise $K$; under greedy search "both
  circuits have similarly large incompleteness scores" [wang-2022 §4.3].

**One-line checkpoint:** faithfulness says the listed parts run the task;
completeness hunts for unlisted spares; minimality checks every listed part
is load-bearing somewhere — and all three are numbers under one knockout.

## What it licenses

- **Faithfulness** licenses: "under {knockout} on {reference}, $C$ alone
  retains {x}% of $F(M)$ on {task}." It does *not* license "C is the
  circuit": the naïve circuit is as faithful as the full one.
- **A large incompleteness score** licenses: "the model has task-relevant
  structure outside $C$ that is exposed when $K$ is removed." A *small* one
  under a given search licenses only "this search did not find such a $K$."
  The paper's own random and class-wise searches were falsely reassuring.
- **A minimality score** licenses: "in the context $C \setminus K$, node $v$
  contributes {amount}." It is a *conditional* necessity claim — the $K$ is
  part of the statement.

## Where it's contested

- **The faithfulness score is not robust to the ablation methodology** —
  Miller et al., added 2026-09-19. Re-evaluating this exact circuit with
  one axis of the [[ablation-methodology]] six-tuple changed at a time:
  edge instead of node ablation gives "substantially higher percentages",
  with a median "well over 100%" at specific positions; resample instead
  of mean is systematically lower (p = 1e−5, node level); ablating all
  positions instead of the circuit's is consistently lower; BABA prompts
  score higher than ABBA; the score rises monotonically with the size of
  the ABC set used for the mean (Wang et al. used about seven examples per
  template); and taking the mean of per-prompt ratios instead of the ratio
  of means gives substantially higher numbers [miller-2024 §4, §4.1, Figs.
  3, 4]. Their conclusion is not that the circuit is wrong but that
  "existing circuit faithfulness scores reflect both the methodological
  choices of researchers as well as the actual components of the circuit"
  [miller-2024 Abstract].
- **Faithful on average, not per prompt.** Under Wang et al.'s own
  methodology the per-prompt logit difference recovered has an
  interquartile range up to 50 points and outliers "in the tens of
  thousands of percent"; "while the circuit matches the behavior on
  average, it does not match it for many examples". Miller et al. ask for
  average *and* worst case, and note a circuit with high variance "is at
  least partially optimized to balance out" very high and very low prompts
  [miller-2024 §4.2, Fig. 4].
- **The criteria presuppose a fixed methodology, and the ground truth does
  not.** In a compiled Tracr model the correct circuit differs between
  zero and resample ablation, because one edge carries only information
  constant across inputs [miller-2024 §5]. Faithfulness, completeness and
  minimality are all $F$-based, so all three inherit this.
- **Two of the three searches said "complete"; the third said "87%
  incomplete".** The disagreement is inside the paper, not between sources.
  Which search strategy a completeness claim used has to be stated with it.
- **The criteria do not discriminate faithful-and-wrong from
  faithful-and-right at the faithfulness level.** That is the paper's
  running example and its own baseline result.
- **Every number is relative to per-position mean ablation on `p_ABC`.**
  `docs/01-methods.md` records Miller et al.'s finding that the scores move
  with the ablation method and the mean's sample size; this page is the
  definition those findings apply to. The reconciliation is an R1 task
  (D-010, item 3).
- **The greedy sets are not interpretable**, so the paper cannot say *what*
  is missing — only that something is. "Investigating them would be an
  interesting direction of future work" [wang-2022 §4.1].

## What this project does with it

- **E2** has a published faithfulness figure to check against (87% under the
  stated knockout) and a published *incompleteness* figure (up to 3.09 under
  greedy search). Reproducing the first without the second would reproduce
  the reassuring half only.
- **E3 does not produce circuits** ([[circuit]]), so these criteria do not
  apply to the heatmaps directly. They apply the moment any subset of heads
  is *named* as "the X circuit" in a writeup.
- **E4:** the completeness failure is self-repair seen from the validation
  side — the model has spares. $M \setminus K$ outperforming $C \setminus K$ is the
  quantity E4's backups produce. See [[self-repair]].
- **D-006** is the reason to compute each criterion under more than one
  knockout, not one.

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: Abstract · 3.4 · 4 · 4.1 · 4.2 · 4.3 · App. K (Fig. 20) ·
  App. M (Algorithm 3, Fig. 22).
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: Abstract · 4 · 4.1 (Figs. 3, 4) · 4.2 · 5.

## Open questions

- Does the greedy incompleteness result survive a change of knockout
  (zero, resample) or of reference distribution? Miller et al. vary the
  *faithfulness* arm only; completeness and minimality under other
  six-tuples remain unmeasured.
- What is the right *reporting* unit for completeness in a results doc —
  the max score found, the search budget, or the full set of $K$s? The paper
  gives all three in an appendix; a reproduction should too.
