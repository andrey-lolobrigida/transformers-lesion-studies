---
title: Head activation evaluators (copying, prefix matching, previous token)
type: method
status: drafted
sources: [olsson-2022, wang-2022]
first-needed: E2
updated: 2026-09-19
---

# Head activation evaluators

## In one sentence

Three cheap behavioural scores — **copying**, **prefix matching** and
**previous token** — computed from a head's activations on synthetic sequences,
used to identify induction heads without reading any weights.

## Claim-licence block

| | |
|---|---|
| **Answers** | A response-profile question: *on this stimulus, does this head attend where induction predicts, and does its direct-path output raise the attended token's logit?* |
| **Does NOT answer** | Necessity or sufficiency. No component is removed and none is restored; a head can score 0.9 and matter for nothing. Also not a mechanism claim — the score is agnostic about how the pattern is produced. |
| **Confounds** | Each score is averaged over **10 examples** of 25 random tokens. Token exclusion, sequence length, repeat count and the presence of a BOS token all move the score, and one of them moved it enough that the authors flag their own omission. Copying is measured on the direct path only, so a head whose output is processed by later layers scores low while still contributing. |
| **Always log** | Number of examples, sequence length, repeat count, the token-exclusion rule, BOS present or absent, seed. Epistemic rule 4's logic applies verbatim: this is a small-sample measurement and small samples manufacture results. |

## Why it exists

[[induction-head]] is defined behaviourally precisely so that it can be measured
in large models with MLPs, where the weight-level analysis is unavailable. These
evaluators are that measurement — "heuristic measurements of attention heads, to
score how strongly a head exhibits specific properties of interest... empirical
measurements, based on observed activations on example data" [olsson-2022
§Data Collection (3)].

The three are chosen to line up with the induction mechanism: copying and prefix
matching *together* make a head an induction head by definition, and
previous-token attention identifies the earlier head that an induction head
composes with.

Note which circuit each depends on, because it determines what a low score can
mean: **copying is an OV-circuit property; prefix matching and previous-token
attention are QK-circuit properties** [olsson-2022 §Data Collection (3)]. See
[[qk-ov-circuits]].

## Precisely

Each score is averaged over **10 examples** [olsson-2022 §Data Collection (3)]:

**Copying.** Generate 25 random tokens, excluding the most common and least
common tokens. Compute the head's contribution to the residual stream and
convert it through the unembedding — the "direct path" — into per-logit effects.
Subtract the mean logit and apply a ReLU, so the score only sees where logits
are *raised*. Take the ratio of the amount it raises the attended token's logit
to that of all tokens in the sample. This ranges 0 (only raises other tokens) to
0.5 (only raises the attended token), rescaled to −1…1.

**Prefix matching.** Generate 25 random tokens with the same exclusions, repeat
the sequence **4 times**, and prepend a start-of-sequence token. Compute the
attention pattern. The score is the average of the attention entries attending
from a given token back to the tokens that *preceded the same token in earlier
repeats*.

The paper flags its own inconsistency here: the BOS token was included for
prefix matching but omitted from the copying evaluator "by mistake" — and
without it, "some heads that were doing prefix matching on real data would get
anomalously low scores on our test sequences" [olsson-2022 §Data Collection
(3)]. A stimulus-formatting detail moved the score enough to be worth an
in-text apology. Any reproduction must match it exactly or report that it did
not.

**Previous token.** Draw an example from the training distribution (not random
tokens). Compute the attention pattern; the score is the average of entries
attending from token *i* to token *i−1*.

**The weight-based counterpart.** A fourth measurement exists as a validation
target: the **trace of QK eigenvalues** for the previous-token QK-circuit term
[olsson-2022 §Data Collection (4)]. It restricts the QK circuit expansion to
pure K-composition terms with earlier heads that attend to the previous token,
weights each such term by how previous-token-like that earlier head is, sums
them, and takes the trace of the resulting `W`. Positive eigenvalues indicate
"same-matching". It is defined only for models deeper than one layer and only
for heads in layer 2 onwards.

**Validation.** On small attention-only models, the copying evaluator correlates
with the fraction of positive OV eigenvalues, and the prefix-matching evaluator
correlates with that QK eigenvalue trace [olsson-2022 §Validating head
activation evaluators]. The empirical scores are therefore checked against the
mechanism *only where the mechanism could be computed* — which is not the
regime this project works in.

**Wang et al.'s variants, run on GPT-2 small** — added 2026-09-19. Stimulus:
sequences of 100 tokens sampled uniformly from the vocabulary, each
duplicated to form `AA` [wang-2022 App. H]. Scores from the attention
patterns:

- *Previous token score*: mean attention on the off-diagonal (position `i`
  to `i−1`). Highest two heads: **4.11, 2.2**.
- *Induction score*: mean attention from `T_i` to the token after the first
  occurrence of `T_i` (i.e. `T_{i−99}`). **5.5 and 6.9** are among the top
  five.
- *Duplicate score*: for each `T_i` in the second half, mean attention to its
  earlier occurrence `T_{i−100}`. **3.0 and 0.1** are among the top three;
  the "fuzzy" duplicate head 0.10 does not appear and, on OpenWebText,
  attends mostly to the current token [wang-2022 App. I].
- *Copy check*: the dot product `⟨h_i(X), W_U[B]⟩` between the head's output
  and the unembedding of the token to be predicted; 5.5 and 6.9 are among the
  20 heads contributing most [wang-2022 App. H, Fig. 17].

Differences from Olsson et al.: 100 tokens × 2 rather than 25 × 4; no BOS
token mentioned; no token exclusions mentioned; copying checked by a raw
dot product rather than the ReLU-and-ratio score. **Rankings are reported,
not values.** A separate **copy score** in the main text (residual stream
at a name after MLP0 × `W_OV` × `W_U` → final LayerNorm → is the name in the
top five; N = 1000) characterises the Name Movers at > 95% against < 20% for
an average head [wang-2022 §3.1]; it is an OV-circuit measurement on a real
residual vector rather than on `W_E`, so it sits between this page and
[[weight-statistics]].

**Joint distribution.** Heads with a positive prefix-matching score are more
likely to have a positive copying score, more strongly so at the highest prefix
scores; the distribution is sharper in small models than full-scale ones
[olsson-2022 §Distribution of scores].

## Where it's contested

- **The two conjuncts come apart at scale.** Above 16 layers, a small number of
  heads score well on prefix search and *negative* on copying — not induction
  heads, and unexplained [olsson-2022 §Additional Curiosities].
- **Correlation with the weight measures is only established for small
  attention-only models.** Extending the evaluators to a model with MLPs is
  exactly the step where the validation is missing, and the paper's framing
  ("heuristic") is honest about it.
- **Direct-path-only copying under-counts.** The translation head scores 0.20 on
  copying while performing translation; the authors' own reading is that its
  output "needs to be further processed by later layers" [olsson-2022 §Behavior
  2: Translation]. A low copying score is weak evidence of not copying.
- **The independent replication used the criterion, not the implementation.**
  Lieberum restates the definition in his own terms and finds candidate heads in
  GPT-2 and GPT-Neo, but reports no scores [olsson-2022 §Replication (Tom
  Lieberum)]. There is no published per-head *score* for GPT-2 small in either
  source. Wang et al. add head *identities* and rankings for GPT-2 small (above),
  on a differently formatted stimulus.

## What this project does with it

- **E2's most reproducible target.** These scores need no ablation, no
  patching, and no battery — a forward pass on synthetic sequences. That makes
  them a good early smoke test on top of E0's published-number check, and a
  cheap way to locate GPT-2 small's induction heads before ablating anything.
  Caveat: neither Olsson et al. nor Wang et al. publish GPT-2 small *scores*;
  Wang et al. publish which heads rank highest (5.5, 6.9; 4.11, 2.2; 3.0,
  0.1). E2 reproduces a method and a ranking, not a number.
- **O-010 candidate 2 is exactly this**, tracked across checkpoints. The E6
  sketch's "two named scores on a plain scatter, animated over checkpoints" is
  prefix matching against copying — the paper's own §Distribution of scores
  plot, over time.
- **A stimulus-parameter table belongs in the E1 battery artifact.** Sequence
  length, repeats, exclusions, BOS. The copying/BOS mistake above is the reason.
- **Not a substitute for the lesion map.** Scoring a head high here says nothing
  about whether the model needs it — which is the whole content of E3. Keeping
  the two apart is epistemic rule 1 in its most tempting failure case: the score
  is a per-head number that looks exactly like an ablation effect on a heatmap.

## Sources

- [olsson-2022] Olsson et al., "In-context Learning and Induction Heads",
  Transformer Circuits Thread, 8 March 2022.
  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
  Sections cited: Data Collection (3) Head activation evaluators · Data
  Collection (4) Trace of QK eigenvalues · Validating head activation
  evaluators · Distribution of scores · Additional Curiosities · Behavior 2 ·
  Replication (Lieberum).
- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 3.1 · App. H (Figs. 17, 18) · App. I.

## Open questions

- **Is 10 examples enough for a stable per-head score on GPT-2 small?** Measure
  it — a variance estimate over seeds costs almost nothing and would set the
  project's own sample size rather than inheriting one.
- **What threshold separates induction heads from the continuum?** Same question
  as on [[induction-head]]; it has to be answered here because this is where the
  number comes from.
