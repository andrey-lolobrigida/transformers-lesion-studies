---
title: QK and OV circuits
type: concept
status: drafted
sources: [elhage-2021, olsson-2022]
first-needed: R0
updated: 2026-09-14
---

# QK and OV circuits

> Rewritten 2026-09-14 from Elhage et al. 2021. The previous version was a
> stub built from Olsson et al.'s summary-by-pointer; what Olsson adds is kept
> under "What this project does with it" and in the sources.

## In one sentence

The **QK circuit** is the bilinear form that scores every (destination, source)
token pair and so determines *where* a head attends; the **OV circuit** is the
linear map that determines *what a source token contributes to the output* if
it is attended to; in a one-layer model both can be multiplied all the way out
to $n_{\text{vocab}} \times n_{\text{vocab}}$ tables and read directly off the weights.

## Why it exists

Because "what does head h do?" is two questions, answered by two disjoint sets
of parameters, and the standard q/k/v presentation hides that. Elhage et al.
show that queries, keys and values are "intermediary by-products" of two
low-rank matrices, $W_{QK} = W_Q^\top W_K$ and $W_{OV} = W_O W_V$, and that "it can be
useful to describe transformers without reference to them" [elhage-2021
§Summary of Results: Conceptual Take-Aways]. Naming the two circuits is what
lets you study one while holding the other fixed — which is the structural
fact underneath [[pattern-preserving-ablation]] and the two induction-head
evaluators on [[head-activation-evaluators]].

## Intuition, then mechanism

**The analogy:** two lookup tables. The QK table answers "when I am at token
*B*, how much do I want to look back at token *A*?" The OV table answers "if I
do look at *A*, which next-token *C* should I bet on?" Read together they spell
a **skip-trigram**, `[A] … [B] → [C]`: the source, the destination, and the
output whose logit is moved [elhage-2021 §Interpretation as Skip-Trigrams].

**Where the analogy breaks — and the paper says so.** A true trigram table is a
function $f(A, B, C)$. What the head stores is a *factored* form, roughly
$f_1(A, B) \cdot f_2(A, C)$: the QK table knows about $A$ and $B$, the OV table about
$A$ and $C$, and neither knows about the pair $(B, C)$. So a head that raises
both `keep … in → mind` and `keep … at → bay` must also raise `keep … in → bay`
and `keep … at → mind`. The authors call these skip-trigram "bugs", observe
them frequently, and note they are probably a good trade for the model on
balance [elhage-2021 §Skip-Trigram "Bugs"]. A second break: the QK table is
only *the* attention computation in a one-layer model. Deeper, the QK circuit
has many terms, one per way information can reach the query and key sides
(see [[attention-head-composition]]).

**Now the mechanism**, for a one-layer attention-only model. Tokens are one-hot
$t$; the stream is $x = W_E t$; logits are $W_U x$. Expand the model into paths
([[path-expansion]]) and each head contributes one term
$A^h \otimes (W_U W_{OV}^h W_E)$, where $A^h = \operatorname{softmax}(t^\top \cdot W_E^\top W_{QK}^h W_E \cdot t)$.
Two $n_{\text{vocab}} \times n_{\text{vocab}}$ matrices appear [elhage-2021 §Splitting Attention Head
terms into Query-Key and Output-Value Circuits]:

- **$W_E^\top W_{QK}^h W_E$ — the QK circuit.** Entry $(\text{query token}, \text{key token})$ is
  "how much a given query token 'wants' to attend to a given key token".
- **$W_U W_{OV}^h W_E$ — the OV circuit.** Entry $(\text{output token}, \text{source token})$
  is "how a given token will affect the output logits if attended to".

The QK circuit is a path traced from two tokens up to the head, where they
meet in a dot product. The OV circuit is a path traced from a token, through
the head's value and output, up to the logits.

**One-line checkpoint:** QK is $x_{\text{dest}}^\top W_{QK}\, x_{\text{src}} \to \text{score}$; OV is
$x_{\text{src}} \to W_{OV}\, x_{\text{src}} \to$ added to $x_{\text{dest}}$; in one layer, wrap both in the
embeddings and they become vocabulary tables.

## Precisely

Per-head matrices (paper's shapes; see the convention warning on
[[attention-head]]):

$$
\begin{aligned}
W_{QK} &= W_Q^\top W_K && [d_{\text{model}}, d_{\text{model}}],\ \operatorname{rank} \le d_{\text{head}} \\
W_{OV} &= W_O W_V && [d_{\text{model}}, d_{\text{model}}],\ \operatorname{rank} \le d_{\text{head}}
\end{aligned}
$$

$$
\begin{aligned}
\text{score}(i, j) &= x_i^\top W_{QK}\, x_j && (\text{destination } i,\ \text{source } j) \\
A_{i,\cdot} &= \operatorname{softmax}_{j \le i}\, \text{score}(i, j) \\
h(x)_i &= \textstyle\sum_j A_{i,j}\, W_{OV}\, x_j
\end{aligned}
$$

**One-layer, token level:**

$$
\begin{aligned}
\text{QK circuit:}\quad C_{QK}^h &= W_E^\top W_{QK}^h W_E && [n_{\text{vocab}}, n_{\text{vocab}}] \\
\text{OV circuit:}\quad C_{OV}^h &= W_U W_{OV}^h W_E && [n_{\text{vocab}}, n_{\text{vocab}}]
\end{aligned}
$$

Both are enormous in expanded form (~2.5 billion entries for a 50k vocabulary)
and rank $\le d_{\text{head}}$ (64 or 128) — "quite small even though they appear large"
[elhage-2021 §Summarizing OV/QK Matrices]. Keep them factored; see
[[weight-statistics]] for the identities.

**Deeper models.** The OV-side logic is unchanged (each head's term is still
$A \otimes W_U W_{OV} W_E$, plus virtual-head terms). The QK circuit is not: the
second-layer score is $x^{1\top} W_{QK}\, x^1$ with $x^1$ containing first-layer writes on
*both* the query and key sides, so it expands into terms of the form
$A_q \otimes A_k \otimes W$, read as $x\,(A_q \otimes A_k \otimes W)\,y = A_q^\top x W y A_k$: $A_q$ moves
query-side information between tokens, $A_k$ moves key-side information, $W$
combines them into a score [elhage-2021 §Path Expansion of Attention Scores QK
Circuit]. Olsson et al.'s $C_{QK}^h$ is this object.

**Two properties worth naming** [elhage-2021 §Detecting Copying Behavior,
§Checking the Mechanistic Theory]:

- A **copying** OV circuit maps tokens toward themselves: attending to $A$
  raises the logit of $A$ (and, to a lesser extent, similar tokens). The
  paper's summary statistic is eigenvalue positivity of $C_{OV}$.
- A **same-matching** QK matrix $W$ (in the composed term above) scores
  highest when query-side and key-side tokens agree. Same statistic, applied
  to $W$.

**What the paper found in one-layer models** [elhage-2021 §Copying / Primitive
In-Context Learning, §Other Interesting Skip-Trigrams, §Detecting Copying
Behavior]:

- Most heads "dedicate an enormous fraction of their capacity to copying": the
  OV circuit raises the attended token, the QK circuit attends back only to
  tokens that could plausibly come next. By the eigenvalue statistic, 10 of 12
  heads in the 12-head model are "significantly copying".
- A special case: heads that handle words split by tokenisation (`" Ralph"`
  vs `"R" + "alph"`), attending from a fragment back to the whole word and
  predicting the continuation — "a very special case where a one-layer model
  can kind of mimic the induction heads we'll see in two layer models".
- Other skip-trigrams encode indentation-sensitive Python keywords, bracket
  matching, LaTeX `\left … \right`, URL structure, fixed phrases. Many depend
  on tokeniser quirks.
- The paper's verdict on whether this "fully understands" a one-layer model:
  yes in the sense that a giant linear regression is understood — "no longer
  any algorithmic mystery", but far too much to hold in one's head
  [elhage-2021 §Do We "Fully Understand" One-Layer Models?].

**Value-weighted attention.** For visualisation the paper scales each
attention weight by the norm of the value vector at the source, $\lVert v_{\text{src}}^h \rVert$,
because heads park on a default position (often the first token) with a small
value vector when nothing matches; the raw pattern then over-reports that
resting position [elhage-2021 §Analyzing a Two-Layer Model].

## What it licenses

Reading the two circuits is a statement about **weights**, and the paper is
careful about what that buys:

- In a one-layer attention-only model the tables *are* the model, up to the
  direct path. "The bigram and skip-trigram tables can be accessed directly
  from the weights, without running the model" [elhage-2021 §Summary of
  Results]. A large entry licenses "this head's OV circuit raises the logit of
  $C$ when $A$ is attended, and its QK circuit attends from $B$ to $A$" — a
  sufficiency-flavoured claim, but only because there is nothing else in the
  model for it to interact with.
- In GPT-2 small, the same tables are one term among many, $W_{OV}$ sits between
  MLPs, and the QK circuit has composed terms. A table entry then licenses only
  "the head's direct-path contribution, with patterns fixed, has this sign and
  size". Whether the model *uses* it is a behavioural question for ablation and
  patching (rules 1–2).
- Three technical caveats the authors state: correlated variables and
  fungibility (a head can carry a zero weight because another head does the
  same job); QK scores are not comparable across different query tokens, with
  "no clear right answer" on normalisation; and "interpretation is not trivial"
  even once the tables exist [elhage-2021 §Interpretation as Skip-Trigrams].

## Where it's contested

- **Copying has no settled formalisation.** The eigenvalue statistic is the
  authors' working choice, not a definition; the diagonal, top-k self-rank and
  trace are alternatives, all linked by $\operatorname{trace} = \sum \text{diagonal} = \sum \text{eigenvalues}$, and
  "copying is actually a more complex concept than it might first appear"
  (gender, plurality, tense heads copy something without copying tokens)
  [elhage-2021 §Detecting Copying Behavior]. Details on [[weight-statistics]].
- **The vocabulary-table form is a one-layer object.** Every later use of "the
  QK circuit" (Olsson's $C_{QK}$) means the multi-term expansion, which is a
  different, larger thing with the same name.
- **Position is outside the tables** in the paper's models; with standard
  positional embeddings the one-layer QK circuit picks up an extra term from
  $W_{QK}$ acting on the positional embeddings [elhage-2021 §Primarily
  Positional Attention Heads]. GPT-2 small is the latter case.

## What this project does with it

- **The E3 direct-effect setting is the OV circuit's direct path.** O-011's
  resolution defines three path-restriction values; "direct effect" is $W_U
  W_{OV}^h$ applied to what the head actually attended, which is this page's OV
  circuit evaluated on the run [elhage-2021 §Splitting…]. Olsson's copying
  evaluator measures the same object empirically [olsson-2022 §Data Collection
  (3)].
- **Olsson's evaluators partition along this line**: copying is an OV
  property; prefix matching and previous-token attention are QK properties
  [olsson-2022 §Data Collection (3)]. A low score on one says nothing about
  the other.
- **E2's induction check** has a weight-side half: a same-matching QK term via
  K-composition plus a copying OV circuit, tested by eigenvalue positivity
  [elhage-2021 §Checking the Mechanistic Theory]. See [[induction-head]].
- **A one-layer-style skip-trigram head is a candidate E3 control**: a head
  whose OV/QK tables are legible from the weights gives the heatmaps a row
  whose expected behaviour is known before ablation. Not scheduled; noted.

## Sources

- [elhage-2021] Elhage et al., "A Mathematical Framework for Transformer
  Circuits", Transformer Circuits Thread, 22 December 2021.
  https://transformer-circuits.pub/2021/framework/index.html
  Sections cited: Summary of Results · Splitting Attention Head terms into
  Query-Key and Output-Value Circuits · OV and QK Independence · Interpretation
  as Skip-Trigrams · Copying / Primitive In-Context Learning · Other
  Interesting Skip-Trigrams · Primarily Positional Attention Heads ·
  Skip-Trigram "Bugs" · Summarizing OV/QK Matrices · Detecting Copying
  Behavior · Do We "Fully Understand" One-Layer Models? · Path Expansion of
  Attention Scores QK Circuit · Analyzing a Two-Layer Model · Checking the
  Mechanistic Theory.
- [olsson-2022] Olsson et al., "In-context Learning and Induction Heads",
  Transformer Circuits Thread, 8 March 2022. Sections cited: Data Collection
  (3) · Summary of Reverse Engineering Induction Heads.

## Open questions

- How should QK scores be normalised across query tokens for any E3 figure
  that compares them? The source says there is no clear answer; whatever E3
  does has to be written down.
- Does GPT-2 small's layer-0 contain heads whose vocabulary tables are legible
  the way the paper's one-layer heads are? Cheap to check at E1; would make the
  control row above real.
