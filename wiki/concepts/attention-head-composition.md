---
title: Attention head composition
type: concept
status: drafted
sources: [elhage-2021, olsson-2022, wang-2022]
first-needed: E2
updated: 2026-09-19
---

# Attention head composition

## In one sentence

Two heads **compose** when a later head's $W_Q$, $W_K$ or $W_V$ reads a
subspace of the residual stream that an earlier head wrote — **Q-** and
**K-composition** change *where* the later head attends, **V-composition**
changes *what it moves* and makes the pair behave as one "virtual" head.

## Why it exists

Without composition, "a two-layer model would simply have more attention heads
to implement skip-trigrams with" [elhage-2021 §Two-Layer Attention-Only
Transformers]. Composition is the whole difference between one and two layers,
and it is what turns a lookup table of skip-trigrams into "something much more
like a computer program running an algorithm". The concept earns a page
because E2's target — the induction head — does not exist without it, and
because "head A feeds head B" is the edge type every circuit diagram on this
project will be drawn with.

## Intuition, then mechanism

**The analogy:** a relay. The first runner (head 1) carries something to a
position in the stream; the second runner (head 2) starts from there. Which
leg of head 2 picks up the baton matters: if head 2's *key* reads it, head 1
has changed what head 2 can be attracted to; if the *query* reads it, head 1
has changed what head 2 is looking for; if the *value* reads it, head 1 has
changed what head 2 carries.

**Where the analogy breaks.** A relay hands over once, to one runner. In the
stream, head 1's write persists and any number of later heads can read any
part of it, so composition is many-to-many. And the handover is a matrix
product in the *weights*: it exists whether or not the model uses it on a given
input. Heads "operate on small subspaces and can easily avoid significant
interaction", and most do [elhage-2021 §Three Kinds of Composition, §Analyzing
a Two-Layer Model].

**Now the mechanism.** Recall the stream is a communication channel and each
head reads it through $W_Q$, $W_K$, $W_V$ and writes through $W_O$. Then
[elhage-2021 §Three Kinds of Composition]:

- **Q-composition:** $W_Q$ reads in a subspace affected by a previous head.
- **K-composition:** $W_K$ reads in a subspace affected by a previous head.
- **V-composition:** $W_V$ reads in a subspace affected by a previous head.

Q and K both affect the attention pattern and "allow attention heads to express
much more complex patterns". V affects what is moved; "composing movement of
information with movement of information gives movement of information", so
V-composed heads reduce to a single unit — the virtual head — "whereas
attention heads affecting attention patterns is not reducible in this way".

**One-line checkpoint:** composition = a later head's read overlapping an
earlier head's write; Q/K change the pattern, V makes a virtual head.

## Precisely

**Virtual attention heads** [elhage-2021 §Virtual Attention Heads]. The
V-composition of $h_1$ then $h_2$ is the term $(A^{h_2} A^{h_1}) \otimes (W_{OV}^{h_2} W_{OV}^{h_1})$ in the logit path expansion: an object with its own pattern
$A^{h_2 \circ h_1} = A^{h_2} A^{h_1}$ and its own OV matrix. Two remarks from the paper:

- The number of ordinary heads grows linearly with depth; two-head virtual
  heads grow quadratically, three-head cubically. Virtual heads may be the
  model's way of doing "small" tasks — copying tense or person — that a full
  head with $d_{\text{head}}$ dimensions is too large for.
- In the two-layer model analysed, the second-order terms have "a pretty
  small marginal effect", measured by the term-importance ablation on
  [[path-expansion]]. The authors expect them to matter more in larger models
  and say so twice.

**The second-layer QK circuit** [elhage-2021 §Path Expansion of Attention
Scores QK Circuit]. Expanding $x^{1\top} W_{QK}^h\, x^1$ with $x^1 = x^0 + \sum h(x^0)$ gives
a sum of terms $A_q \otimes A_k \otimes W$, one for each (query-side head or identity,
key-side head or identity) pair. The $\mathrm{Id} \otimes \mathrm{Id} \otimes W_E^\top W_{QK} W_E$ term is the
one-layer table; a term $\mathrm{Id} \otimes A^{h_1} \otimes W_E^\top W_{QK}^{h_2} W_{OV}^{h_1} W_E$ is
K-composition with $h_1$; the mirror is Q-composition.

**The minimal induction term.** K-composition with a previous-token head
$h_{-1}$ produces $\mathrm{Id} \otimes A^{h_{-1}} \otimes W$. If $W$ is same-matching — "the QK version of
a 'copying matrix'" — the term raises the score at source $j$ when the token
*before* $j$ matches the destination token [elhage-2021 §How Induction Heads
Work]. Other two-layer models grow a head attending slightly further back,
presumably to add an $A^{h_{-1}} \otimes A^{h_{-2}} \otimes W$ term.

**Composition scores** [elhage-2021 §Analyzing a Two-Layer Model], normalised
Frobenius norms of the relevant virtual weight, with the empirical value for
random matrices of the same shape subtracted:

$$
\begin{aligned}
\text{Q:}\quad & \lVert W_{QK}^{h_2\top} W_{OV}^{h_1} \rVert_F \,/\, \big(\lVert W_{QK}^{h_2\top} \rVert_F\, \lVert W_{OV}^{h_1} \rVert_F\big) \\
\text{K:}\quad & \lVert W_{QK}^{h_2} W_{OV}^{h_1} \rVert_F \,/\, \big(\lVert W_{QK}^{h_2} \rVert_F\, \lVert W_{OV}^{h_1} \rVert_F\big) \\
\text{V:}\quad & \lVert W_{OV}^{h_2} W_{OV}^{h_1} \rVert_F \,/\, \big(\lVert W_{OV}^{h_2} \rVert_F\, \lVert W_{OV}^{h_1} \rVert_F\big)
\end{aligned}
$$

Licence and caveats for these are on [[weight-statistics]].

**What the analysed model showed.** Body text: only significant K-composition,
with a single layer-0 head whose pattern attends mostly to the previous token
(and less to the present and two back); no significant Q- or V-composition;
most heads in no composition at all. **Correction, post-publication:** a bug
in the low-rank library computed a different quantity — one that happens to
respond strongly to exactly the previous-token K-composition an induction head
uses and filter out other kinds — so the diagram understated composition.
Corrected: previous-token K-composition unchanged in importance, plus two of
the induction heads also rely on a head attending to the last several tokens
[elhage-2021 §Analyzing a Two-Layer Model, §Correction: Attention Head
Composition Diagram].

**All three kinds, observed behaviourally in GPT-2 small** — added
2026-09-19 from Wang et al., who find each by [[path-patching]] into a
specific input of the receiving heads, not from composition scores:

| Kind | Sender → receiver input | Heads | Where |
|---|---|---|---|
| Q-composition | S-Inhibition → Name Movers' **queries** at END | 7.3, 7.9, 8.6, 8.10 → 9.6, 9.9, 10.0 | §3.2 |
| K-composition | Previous Token → Induction heads' **keys** at S1+1 | 4.11, 2.2 → 5.5, 6.9 | App. D |
| V-composition | Duplicate Token, Induction → S-Inhibition **values** at S2 | 0.1, 3.0, 5.5, 6.9 → S-Inhibition | §3.3 |

The paper names the V case explicitly — S-Inhibition heads "output
information about the position of S1 but don't attend to it directly. They
thus must rely on the output of other heads through value composition"
[wang-2022 §3.2] — and the K case as "key composition with Previous Token
Heads" [wang-2022 App. D]. The weight-level counterpart (composition scores,
eigenvalues) is listed among the validations the authors did not perform
[wang-2022 §3.3]. So for these heads the behavioural half of the licence
below exists and the parameter half does not — the mirror image of the
Elhage et al. situation.

## What it licenses

A non-zero composition score licenses: *at the weight level, head $h_2$'s
{query | key | value} read overlaps head $h_1$'s write more than random matrices
of the same shape would.* It is a statement about parameters.

It does **not** license "$h_1$ feeds $h_2$" as a behavioural claim on any dataset.
The paper's own next move after finding the K-composition was to look at
attention patterns on text and then on random repeated sequences, and only
then to state the mechanism [elhage-2021 §Function of Induction Heads]. On
this project, the behavioural half is an ablation (necessity) or a patching
result (sufficiency), never the score alone.

## Where it's contested

- **The paper's own composition diagram was wrong**, see above. Any number
  quoted from the original figure is quoting the erratum.
- **"Composition is rare" was an artefact of the bug** in part. The corrected
  view is still that most heads compose little, but the sentence "there is only
  significant K-composition, and only with one layer 0 head" no longer holds
  for the analysed model.
- **V-composition's importance is stated for one small model.** The authors
  explicitly decline to generalise; the count argument (quadratic growth)
  suggests it may matter more at scale.
- **GPT-2 has an alternative route to induction that uses Q-composition** on
  positional embeddings, unavailable to the paper's models [elhage-2021
  §Pointer Arithmetic with Positional Embeddings]. See [[induction-head]] and
  O-012. Wang et al. looked for that route on IOI — path patching into the
  Induction heads' queries at S2 — and "did not find any significant effect"
  [wang-2022 App. D]. One task, behavioural; recorded on O-012.

## What this project does with it

- **E2** looks for the K-composition structure in GPT-2 small: a
  previous-token head in an early layer and later heads whose $W_{QK} W_{OV}^{\text{prev}}$
  is large and same-matching. The composition scores are cheap and run before
  any ablation. If the pointer-arithmetic route is what GPT-2 small uses, the
  K-score will be small and the Q-score large; that is a result either way.
- **E5 (circuit motifs)** — Q/K/V-composition are the three edge types a
  head-level circuit diagram can have; the previous-token → induction pair is
  the first motif in the catalogue.
- **O-010 candidate 3** ("weights only: the K-composition score between a
  previous-token head and a candidate induction head, over checkpoints") is
  this page's K formula tracked over training.
- **O-011.** Pattern-preserving ablation removes exactly the Q- and K-
  composition routes from an ablation's reach and leaves V-composition. That
  is a cleaner statement of what the three path-restriction values partition
  than the one recorded in the resolution, and should be folded into the E1
  design note when it is written.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Two-Layer Attention-Only Transformers · Three Kinds of
  Composition · Path Expansion of Logits · Path Expansion of Attention Scores QK
  Circuit · Analyzing a Two-Layer Model · Function of Induction Heads · How
  Induction Heads Work · Virtual Attention Heads · Correction: Attention Head
  Composition Diagram · Pointer Arithmetic with Positional Embeddings.
- [olsson-2022] Olsson et al., 2022, §Summary of Reverse Engineering Induction
  Heads — the same mechanism restated, plus the GPT-2 Q-composition remark.
- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 3.2 · 3.3 · App. D.

## Open questions

- Does a previous-token head deserve its own page? Decided **no** for now:
  its content is one positional $A$ and a copying-into-a-subspace $W_{OV}$, fully
  stated here and on [[induction-head]].
- What composition baseline should E2 subtract? The paper subtracts "the
  empirical expected amount for random matrices of the same shapes" without
  giving the sampling procedure. Whatever E2 does is a recorded choice.
