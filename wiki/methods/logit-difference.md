---
title: Logit difference
type: method
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E1
updated: 2026-09-19
---

# Logit difference

## In one sentence

The model's logit for the correct answer token minus its logit for a named
incorrect one — here `logit(IO) − logit(S)` — averaged over a dataset; the
project's default metric (epistemic rule 5) and the metric behind every
number in Wang et al.

## Claim-licence block

| | |
|---|---|
| **Answers** | "How strongly does the model prefer the correct candidate *over this specific competitor*?" A targeted, two-token question. |
| **Does NOT answer** | Whether the correct token is the *top* prediction (that is a different statistic; the paper reports it separately as the proportion with IO over S, and IO probability as a third). Whether behaviour elsewhere in the vocabulary changed. Anything about loss. |
| **Confounds** | The choice of competitor defines the metric — IO vs S is a design decision, and the adversarial datasets change which competitor matters. Direction of change under damage is not always "down": Negative Name Movers *raise* it when ablated. Per-head projections onto `W_U[IO] − W_U[S]` skip the final LayerNorm's scaling (stated approximation). |
| **Always log** | Which two tokens; the dataset and its size; whether the number is a mean over samples or a per-sample distribution; model revision hash. |

## Why it exists

A loss over a 50k-token vocabulary dilutes a two-name decision. Wang et al.
"use two different metrics: logit difference and IO probability. Logit
difference measures the difference in logit value between the two names,
where a positive score means the correct name (IO) has higher probability"
[wang-2022 §2]. The paper then uses logit difference for every intervention
result and IO probability only for the headline performance table.

The page exists because rule 5 makes this the default and confusing it with
loss would change every number in E3; the wiki README names it as the
example of a concept that earns a page.

## Precisely

For an input `X` with indirect object `IO` and subject `S`,
`f(X) = logit_IO(X) − logit_S(X)` at the final position. Reported as a mean
over `p_IOI`. Baselines [wang-2022 §2, §4.4, Fig. 8]:

| Distribution | Mean logit diff | IO probability | S over IO |
|---|---|---|---|
| `p_IOI`, 100,000 samples (§2) | 3.56 | 49% | 0.7% (IO over S 99.3%) |
| `p_IOI` (Fig. 8) | 3.55 | 0.49 | 0.7% |
| Extra occurrence of S (control) | 3.64 | 0.59 | 0.4% |
| Extra occurrence of IO (adversarial) | 1.23 | 0.36 | 23.4% |

The two `p_IOI` rows differ in the second decimal (3.56 vs 3.55; App. A's
baseline is also 3.55 and its prefix-length control reports 3.56 before
patching). Sample sizes differ between experiments; the paper does not
reconcile them and neither does this page.

**Per-head version.** To attribute the difference to a head, the paper takes
the dot product of the head's output at END with an unembedding vector,
`⟨h_i(X), W_U[N]⟩`, for `N` ∈ {IO, S}, and scatters it against the head's
attention to that name (ρ > 0.81, N = 500 for the Name Movers) [wang-2022
§3.1, Fig. 3c]. The final LayerNorm is skipped: "these dot products computed
are not appropriately scaled … approaches to approximating the composition
of attention head outputs with this layer norm were complicated, and resulted
in similar correlation and scatter plots" [wang-2022 §3.1, fn. 1].

**As a circuit score.** `F(C) = E[f(C(X); X)]` — the same metric, evaluated
on the knocked-out model — is what [[circuit-validation-criteria]] are
computed from [wang-2022 §4].

**Logit difference recovered** — Miller et al.'s name for Wang et al.'s
faithfulness ratio, added 2026-09-19:

    (F(x)_correct − F(x)_incorrect) / (M(x)_correct − M(x)_incorrect) × 100

100% means the ablated model matches the full model; negative means the
incorrect token wins; over 100% means the ablated model prefers the correct
token *more* than the full model does [miller-2024 §4]. **Averaging order
matters:** Wang et al. take the ratio of the two *mean* logit differences,
`E[F] / E[M]`; the mean of per-prompt ratios, `E[F / M]`, "return[s]
substantially higher percentages" [miller-2024 §4.1, Fig. 4]. Per-prompt
ratios have an interquartile range up to 50 points on IOI and extreme
outliers (a prompt whose full-model logit difference is near zero makes the
ratio explode) [miller-2024 §4.2].

## What it licenses

A change in mean logit difference under an intervention licenses a claim
about the model's *preference between two named tokens* on that dataset.
Rule 1 phrasing: "…changes mean IO−S logit difference by {amount} over {N}
samples."

It does not license claims about accuracy (top-1) without the companion
statistic, and a per-head projection does not license a claim about the
head's effect *after* the final LayerNorm — the paper's footnote is the
caveat to carry.

## Where it's contested

- **Sign under damage is not uniform.** Ablating a Negative Name Mover
  increases the metric [wang-2022 §3.1]; O-009's addendum already asks each
  battery item to declare the expected direction. This is the IOI instance.
- **The competitor is a choice.** On the adversarial set, the model's
  failure is S over IO 23.4% of the time, but the S-Inhibition heads also
  attend to the second IO — behaviour "beyond the analysis" [wang-2022 §4.4].
  A metric with a fixed competitor cannot see what the model does with a
  third candidate.
- **Loss is never reported** for any intervention in the paper, so there is
  no within-source comparison of the two metrics.
- **The ratio form is unstable per prompt.** Miller et al.'s spread and
  outliers are a property of dividing by a per-prompt denominator that can
  be near zero, not only of the circuit. A results doc that reports
  `E[F/M]` without the distribution is reporting the outliers.

## What this project does with it

- **E1:** every battery item names its correct and competitor tokens and
  logs `N`. IOI inherits IO vs S directly.
- **E3:** heatmaps are in this metric; a written reason is required per
  item to use loss instead (rule 5).
- **Expected direction** per item (O-009 addendum) is recorded next to the
  metric definition; for IOI, "negative" heads are the known exception.

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 2 · 3.1 (incl. fn. 1, Fig. 3c) · 4 · 4.4 (Fig. 8) · App. A.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 4 · 4.1 (Fig. 4) · 4.2.

## Open questions

- ~~Should E1 report the per-sample *distribution* of the difference and not
  only its mean?~~ Yes — Miller et al. show why (2026-09-19). E1 reports
  `E[F]/E[M]`, `E[F/M]`, and the per-prompt interquartile range.
