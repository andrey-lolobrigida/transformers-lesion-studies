---
title: Induction head
type: concept
status: drafted
sources: [olsson-2022, elhage-2021, wang-2022]
first-needed: E2
updated: 2026-09-19
---

# Induction head

## In one sentence

An induction head is an attention head that, given `… [A][B] … [A]`, attends
back to the `[B]` that followed the earlier `[A]` and raises its logit —
completing the pattern by copying what happened last time.

## Why it exists

The concept arrives from two directions at once, and keeping them apart is the
single most important thing on this page.

**Mechanistically**, it was found in Elhage et al. 2021 as a circuit that could
be read off the weights of a two-layer attention-only model — the thing the
model was *doing* in a case small enough to be fully accounted for.

**Empirically**, Olsson et al. needed a definition that survives in models with
40 layers and MLPs, where reading the weights is not currently possible. So
they re-define the induction head **behaviourally**, in terms of what it does on
a repeated random sequence, and then argue that the behavioural and mechanistic
pictures coincide for the small models where both are available
[olsson-2022 §Induction Heads].

The paper is explicit that the earlier treatment was vague: "we were a bit
vague on the exact definition of induction heads: it was more like we found a
cluster of behaviors and mechanisms that tended to occur together, and called
heads in that cluster 'induction heads'" [olsson-2022 §Induction Heads]. The
narrow behavioural definition is the fix.

For this project, that history is the reason to always say *which* definition a
claim is using. "Head 5.5 is an induction head" is three different claims
depending on whether it means the head scores highly on prefix matching, that
its OV circuit has positive eigenvalues, or that it participates in a
K-composition circuit with a previous-token head.

## Intuition, then mechanism

**The analogy the authors chose** is inductive reasoning: if `A` was followed by
`B` earlier in this context, `A` is more likely to be followed by `B` again.
"Induction heads crystallize that inference" [olsson-2022 §Induction Heads].
Note the qualifier — induction *over the context*, not over the training data.
A bigram table is induction over the training data and is a different object.

**Where the analogy breaks.** Calling it "induction" suggests the head is
reasoning about evidence. It is not: it is a fixed pattern-completion rule that
applies "regardless of what A and B are". The paper leans on exactly this to
argue induction heads are not memorised statistics — because the rule
"significantly decouples A and B", the head has no fixed bigram table to update,
and can work out of distribution as long as early-context statistics resemble
late-context ones [olsson-2022 §Induction Heads].

**Now the mechanism**, which needs two heads in different layers:

1. A **previous-token head** in an earlier layer copies information about token
   `i-1` into position `i`. This is what makes it possible for a later head to
   attend to a token based on *what came before it* rather than on its own
   content.
2. The **induction head** in a later layer uses that shifted information to
   find positions whose predecessor matches the current token, and copies the
   token it lands on into the output logits.

This is why induction heads cannot exist in a one-layer model: "an individual
attention head computes attention scores only from the source and destination
token", so without a subspace written by an earlier head, the score for an
attended token cannot depend on the token preceding it [olsson-2022 §Argument
2]. The paper treats the one-layer case as a natural control, and it behaves
as predicted — no induction heads, and almost no in-context learning.

**One-line checkpoint:** a previous-token head shifts information back by one
position; the induction head matches on that shifted information and copies
forward.

## Precisely

The formal definition is behavioural and has two conjuncts, measured **on a
repeated sequence of random tokens** [olsson-2022 §Induction Heads]:

> **Prefix matching:** the head attends back to previous tokens that were
> followed by the current and/or recent tokens.
>
> **Copying:** the head's output increases the logit corresponding to the
> attended-to token.

Both are measured, not asserted; the operational scores are on
[[head-activation-evaluators]]. The paper notes the properties are never
exhibited perfectly — "our measurements give us a continuum, but there is a
clear subset of heads which exhibit these properties with much greater than
random chance". **There is no threshold given.** Any binary "is / is not an
induction head" in this project is a threshold this project chose, and it has to
be recorded as such.

The choice of *random* tokens is deliberate and worth copying: it rules out a
head that heuristically attends to plausible continuations, since on random
tokens nothing is plausible except by repetition [olsson-2022 §Induction Heads].

**The mechanism, as Elhage et al. 2021 first stated it** — extracted
2026-09-14; the composition machinery is on [[attention-head-composition]] and
the circuits on [[qk-ov-circuits]]:

- **Function.** "Induction heads search over the context for previous examples
  of the present token. If they don't find it, they attend to the first token
  (in our case, a special token placed at the start), and do nothing. But if
  they do find it, they then look at the next token and copy it"
  [elhage-2021 §Function of Induction Heads]. The comparison the paper draws:

  | Model | Rule |
  |---|---|
  | One-layer copying head | `[b] … [a] → [b]` |
  | One-layer, tokenisation quirk | `[ab] … [a] → [b]` |
  | Two-layer induction head | `[a][b] … [a] → [b]` |

  The two-layer rule "knows how the token was previously used", makes more
  confident predictions, and "is less vulnerable to distributional shift,
  since it doesn't depend on learned statistics about whether one token can
  plausibly follow another". The random-repeated-sequence test, which Olsson
  et al. turn into the definition, originates here as "likely the hardest test
  one can give them" [elhage-2021 §Function of Induction Heads].
- **Mechanism.** "The central trick to induction heads is that the key is
  computed from tokens shifted one token back. The query searches for
  'similar' key vectors, but because keys are shifted, finds the next token."
  The minimal implementation is K-composition with a previous-token head,
  giving a QK term `Id ⊗ A^{h₋₁} ⊗ W` in which `W` is same-matching
  [elhage-2021 §How Induction Heads Work]. Induction heads "can be more
  complicated than this": other two-layer models add a head attending further
  back, presumably for an `A^{h₋₁} ⊗ A^{h₋₂} ⊗ W` term.
- **Check.** The theory predicts a copying OV matrix and a same-matching QK
  term; plotted on (QK positivity, OV positivity), "all the induction heads
  turn out to be in an extreme right hand corner". The authors pre-empt the
  circularity worry: heads were chosen for *large* K-composition, which does
  not imply *positive* eigenvalues [elhage-2021 §Checking the Mechanistic
  Theory]. Statistic on [[weight-statistics]].
- **In the analysed model**, induction heads are the only thing composition
  is used for, and the layer-0 head they compose with attends "primarily to
  the previous token, and to a lesser extent the present token and the token
  two back" [elhage-2021 §Analyzing a Two-Layer Model]. The post-publication
  correction adds that two induction heads also rely on a head attending over
  the last several tokens [elhage-2021 §Correction: Attention Head Composition
  Diagram].

**The same mechanism as Olsson et al. restate it** [olsson-2022 §Summary of
Reverse Engineering Induction Heads]:

- **Copying is done by the OV circuit**, characterised by *positive
  eigenvalues*. Induction heads are a subset of the copying heads a transformer
  contains.
- **Prefix matching is done by the QK circuit via K-composition**: the induction
  head's `W_K` reads from a subspace written by an earlier head. The basic form
  produces a QK term `Id ⊗ h_prev ⊗ W` with `W` having positive eigenvalues,
  which makes the head compare the *current* token against every earlier
  position's *preceding* token.
- The attention pattern and the output are computed by separable circuits. For
  the attention pattern, the content of the attended token is "quite
  irrelevant"; for the output it is everything.

**The fuzzy generalisation.** The hypothesis the paper is actually arguing is
larger than literal copying: that the same heads implement `[A*][B*] … [A] →
[B]` where `A* ≈ A` and `B* ≈ B` in some representation — an "in-context
nearest neighbours" [olsson-2022 §Induction Heads]. Three heads in the 40-layer
model are shown doing this while still scoring as induction heads on random
sequences [olsson-2022 §Argument 4]:

| Head | Layer | Copying score | Prefix matching score |
|---|---|---|---|
| Literal copying | 21 / 40 | 0.89 | 0.75 |
| Translation | 7 / 40 | 0.20 | 0.85 |
| Pattern matching | 8 / 40 | 0.69 | 0.94 |

*Source inconsistency, recorded not resolved:* the table gives the
pattern-matching head as layer 8, while the prose introducing the same
behaviour says "an attention head (found at layer 26 of our 40-layer model)"
[olsson-2022 §Behavior 3: Pattern matching]. Do not cite a layer number for
that head without checking the figure itself. (Similarly, §Argument 4 says
"up to 12B parameter models" where the model table gives the 40-layer model as
13B non-embedding parameters.)

## What it licenses

An observation that a head scores highly on prefix matching **and** copying
licenses: *under these two evaluators, on repeated random sequences, this head
attends to prefix-matched positions and raises the attended token's logit.* That
is a statement about a measured response profile.

It does **not** license, on its own:

- **That the head is necessary for any behaviour.** That requires an ablation,
  which is a separate experiment [[pattern-preserving-ablation]].
- **That the head is sufficient to produce in-context copying.** Nothing in the
  definition is a patching result (epistemic rule 2).
- **That the head does the abstract version.** Argument 4 shows *particular
  heads* doing translation and pattern matching. The paper's own framing is
  "plausibility", the weakest cell in its evidence tables. Generalising from
  three anecdotal heads in a 40-layer model to induction heads at large is the
  step the authors explicitly decline to take.

The reverse direction matters for E2: a head that fails the evaluators is not
thereby shown to be uninvolved in induction. The evaluators are heuristics with
a stated small sample (10 examples).

## Where it's contested

- **The mechanism is not universal across models — and GPT-2 is the exception
  that matters here.** In the models Olsson et al. study, prefix matching works
  by K-composition with a previous-token head. But "in GPT-2, we've seen
  evidence of a second 'pointer-arithmetic' mechanism": an earlier head attends
  to previous copies of the current token and copies their *positional
  embedding* into the present token; the induction head then uses
  **Q-composition** to rotate that position embedding one token forward
  [olsson-2022 §Summary of Reverse Engineering Induction Heads]. Their own
  models cannot use this mechanism because they do not add positional
  information into the residual stream. **This project's model is GPT-2 small.**
  Any weight-based induction test taken from this paper may be testing for the
  wrong mechanism.

  *The original source of that claim*, now read: "We observed at least one
  case in GPT-2 where an induction head was implemented using this approach,
  instead of the one described above. First, an attention head attended to a
  similar token, returning its positional embedding. Next, a query vector for
  another attention head was constructed with q-composition, rotating the
  positional embedding forward one token" [elhage-2021 §Pointer Arithmetic
  with Positional Embeddings]. One case; no model size, head index or figure.
  It establishes that the route exists in *some* GPT-2, nothing more. Proposed
  as O-012.
- **In the IOI circuit, GPT-2 small's induction heads do not do induction.**
  Heads 5.5 and 6.9 pass Olsson et al.'s prefix-matching and copying tests
  on repeated random tokens [wang-2022 App. H], but in the IOI task their
  output "is used both as a pointer to S1 and as a signal that S is
  duplicated" — a *position* signal consumed by the S-Inhibition heads'
  values, not a copied token. "In the context we study, Induction Heads
  perform a different function compared to what was described in their
  original discovery … We did not investigate how this mechanism was
  implemented" [wang-2022 §3, §3.3]. Two further heads, 5.8 and 5.9, attend
  to S1+1 weakly or diffusely and are called "fuzzy Induction Heads"
  [wang-2022 App. C]. The behavioural definition and the role in a given
  circuit come apart; see [[ioi-circuit]].
- **Prefix-matching heads that are not induction heads.** Above 16 layers, the
  full-scale models "start to show a small number of heads that score well on
  'prefix search', but get a negative score on copying, which means they are
  not induction heads" [olsson-2022 §Additional Curiosities]. The two conjuncts
  come apart.
- **An induction head with the opposite ablation effect.** In the 6-layer MLP
  model, "one lone induction head whose ablation has the opposite effect on the
  in-context learning score" — logged by the authors as unexplained
  [olsson-2022 §Additional Curiosities].
- **A non-induction head that mimics the phase change.** The 6-layer
  attention-only model has a head that is *not* an induction head, yet ablating
  it resembles reversing the phase change [olsson-2022 §Additional Curiosities].
  A head can be central to what changed without matching the definition.
- **The published definition was corrected after publication.** The 2022-09-20
  change log entry fixes the prefix-matching wording in two places, which had
  said "tokens that were *preceded* by the current token" instead of "followed
  by" [olsson-2022 §Change Log]. Secondary sources quoting the original wording
  are quoting an erratum.
- **Independent replication is solid on the small-model mechanism.** Redwood
  Research reliably found induction heads in two-layer attention-only models,
  with previous-token heads in layer 0 and induction heads in layer 1.
  Substituting an idealised previous-token attention pattern recovered 99% of
  the loss difference from ablating that head; an idealised induction pattern
  recovered about 65%, rising ~10% more when `[A][B][C] … [A][B] → [C]` matching
  was included [olsson-2022 §Replication (Adam Scherlis)].

## Where they are found

Location varies systematically with architecture, which is a useful prior for
E2 and a caution against assuming a fixed depth [olsson-2022 §Where induction
heads form]:

| Model family | Where induction heads form |
|---|---|
| Small attention-only (1–6L) | The last layer |
| Small with MLPs (5L, 6L) | More in the second-to-last layer |
| Full-scale (24L, 40L) | Majority before the halfway point in depth |

For GPT-2 specifically the datapoint comes from the invited replication, not
from the authors: induction heads in GPT-2 and GPT-Neo "mostly starting in the
mid-depth region", with GPT2-XL layer 21 head 20 and GPT-Neo-2.7B layer 12 head
0 named as examples [olsson-2022 §Replication (Tom Lieberum)]. Neither is
GPT-2 small. *Added 2026-09-19:* Wang et al. supply GPT-2 small indices —
**5.5 and 6.9** are "among the 5 heads with the highest induction score" on
100-token repeated random sequences and among the 20 largest contributors to
next-token prediction there; **4.11 and 2.2** are the two highest
previous-token heads [wang-2022 App. H]. Rankings, not scores, and on a
stimulus that differs from Olsson et al.'s (100 tokens × 2 repeats, no BOS
mentioned). E2 has head indices to expect, and a stimulus-format difference
to match or declare.

## What this project does with it

- **E2 reproduces this.** The roadmap requires finding the induction head by
  ablation *and* verifying by patching. This page supplies the definition to
  reproduce against; the scores are on [[head-activation-evaluators]].
- **E1's induction battery item** — "induction / in-context copying, synthetic,
  easy to generate cleanly" — is essentially this paper's prefix-matching
  stimulus: a random token sequence, repeated. The generator should record the
  sequence length, the number of repeats, the token-exclusion rule and the
  BOS-token choice, because the paper shows all four change the score.
- **O-010, candidate 2** proposes tracking behavioural head scores over Pythia
  checkpoints as the E6 observable. That is this paper's own figure, which is
  what makes it the reproducible option.
- **D-003 is vindicated at this level**: the unit of analysis here is the head,
  and there is a published, checkable definition at that granularity.

## Sources

- [olsson-2022] Olsson, Elhage, Nanda, Joseph, DasSarma, Henighan, Mann, Askell,
  Bai, Chen, Conerly, Drain, Ganguli, Hatfield-Dodds, Hernandez, Johnston,
  Jones, Kernion, Lovitt, Ndousse, Amodei, Brown, Clark, Kaplan, McCandlish &
  Olah, "In-context Learning and Induction Heads", Transformer Circuits Thread,
  8 March 2022.
  https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html
  Sections cited: Induction Heads · Argument 2 · Argument 4 · Behavior 3 ·
  Summary of Reverse Engineering Induction Heads · Where induction heads form ·
  Additional Curiosities · Change Log · Replication (Scherlis) · Replication
  (Lieberum).
- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Function of Induction Heads · How Induction Heads Work ·
  Checking the Mechanistic Theory · Analyzing a Two-Layer Model · Correction:
  Attention Head Composition Diagram · Pointer Arithmetic with Positional
  Embeddings.
- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 3 · 3.3 · App. C · App. D · App. H.

## Open questions

- **Which mechanism does GPT-2 small use?** K-composition with a previous-token
  head, or the positional pointer-arithmetic route? Elhage et al. report "at
  least one case in GPT-2" of the latter, with no size, head or figure; Olsson
  et al. repeat it. Reading did not settle it. **Proposed as O-012**, to be
  settled at E2 by measurement: the K- and Q-composition scores on
  [[weight-statistics]] make the two routes distinguishable from the weights
  before any ablation. *Evidence added 2026-09-19:* on IOI, path patching
  finds the K-route — Previous Token heads 4.11 and 2.2 affect logit
  difference through the Induction heads' keys at S1+1 — and, testing the
  Q-route directly, "did not find any significant effect" on the Induction
  heads' queries at S2 [wang-2022 App. D]. Behavioural, one task, four heads;
  the weight-level check E2 plans is still the resolution.
- **What threshold makes a head an induction head in this project?** The source
  gives a continuum and no cutoff. Whatever is chosen belongs in the E1 harness
  config and in every result doc that uses it.
- ~~Does a previous-token head deserve its own page?~~ Decided no at the
  Elhage extraction (2026-09-14): it is one positional attention pattern plus a
  `W_OV` that copies token identity into a subspace, fully stated on
  [[attention-head-composition]].
