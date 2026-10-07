# 01 — Methods: what each measurement actually licenses

This is the most important reference document in the project. The
methodological content is easy; the discipline about what each method entitles
you to claim is the hard part, and it's where the project's credibility lives.

## The core distinction

**Ablation tests necessity.** Remove the component, see if behaviour breaks.
Answers: "does the model need this?"

**Activation patching tests sufficiency — in one direction only.** Take a
run on a corrupted input, patch in clean activations from one component, see
if correct behaviour is restored. Answers: "is this enough to produce the
behaviour, given this corruption?" That is the *restore-clean* direction
(Meng et al.'s causal tracing). The same operation run the other way —
clean input, corrupted activations patched in — is a necessity test, and it
is the direction Wang et al. actually use. Miller et al. make direction an
explicit axis of the ablation methodology. A result doc states which run
received the patch; "activation patching" without that qualifier names an
operation, not a claim. Wiki: `wiki/methods/activation-patching.md`.

**Causal scrubbing and faithfulness tests check the whole story.** Answers:
"does my proposed circuit actually explain the behaviour, or have I found a
subgraph that correlates with it?"

Necessity and sufficiency are not the same property, and neither implies the
other. A component can be necessary without being sufficient (it's one step in
a chain), or sufficient without being necessary (there's a redundant path). A
large fraction of overclaiming in this area is a necessity result written up in
sufficiency language. Use the words explicitly in every result summary.

## The methods, and what each is for

### Zero-ablation

Set the component's output to zero. Cheap, easy, and it moves the model
off-distribution: the resulting internal state is one no input could produce.

The standard critique is that this makes zero-ablation "wrong." That's too
simple. Zero-ablation removes both the information the component carried *and*
its baseline contribution to the residual stream — so it answers a broader
question than mean-ablation does.

### Mean-ablation

Replace the component's output with its average over some dataset. Keeps
activations closer to the training distribution and removes the
input-dependent information while preserving the average contribution.

### The point that reframes both

Miller, Chughtai & Saunders (2024, arXiv 2407.08734) found that circuit
faithfulness scores are highly sensitive to seemingly minor changes in ablation
methodology, and drew the conclusion that matters here: **the ablation
determines the task.**

Their worked example, on the IOI circuit: if you want the circuit to include
the mechanism that decides "a name goes here," zero-ablate. If you want the
circuit that, *given* that a name is being produced, picks the right one,
mean-ablate. These are different questions with different correct answers.
Neither is the refined version of the other.

They also found the IOI faithfulness score "monotonically increases with
the size of the ABC dataset" the mean is computed over [miller-2024 §4.1,
Fig. 4]. Their own means use 100 ABC prompts; they report Wang et al.'s as
"around seven examples per template", a figure Wang et al.'s text does not
state. **No mechanism for the effect is given in the paper** — an earlier
draft of this doc attributed one ("noisy means push the model toward
specific wrong answers") that is not in the text, and it is withdrawn. The
consequence stands without it: the set size is part of the measurement, and
a number reported without it is not reproducible. Wiki:
`wiki/methods/mean-ablation.md`.

**Consequences for this project:**

- Always run zero and mean, report both, never pick one.
- Log the mean-ablation dataset size next to every mean-ablation number.
- When the two disagree, treat the disagreement as the result to investigate,
  not noise to resolve.
- Also consider resample ablation (replace with the component's output on a
  different input from the same distribution) as a third point of comparison;
  it stays in-distribution differently again.

### Activation patching / causal tracing

Run on a clean input, cache activations. Run on a corrupted input. Patch clean
activations back in and measure how much correct behaviour is restored. This
is the restore direction described above; it is what phase E2 uses to verify
the reproduction, and the E2 results doc says so in those words.

Two details of the reference implementation (Meng et al., GPT-2 XL) that a
naive reading of "one component at a time" gets wrong. First, the unit
restored: single hidden states for the main map, but for MLP and attention
modules single-layer restorations were "generally negligible", so the
module maps restore **windows of ten consecutive layers** and plot the
result at the centre [meng-2022 App. B.2]. A per-layer map of single
restorations can read as blank where the mechanism is spread across layers.
Second, the metric: the paper reports the *probability* of the correct
token, not a logit difference, so this project's factual-recall numbers are
a translation and are reported next to the probability version until the
two are shown to agree (O-009). Nothing in the paper is measured on GPT-2
small. Wiki: `wiki/methods/causal-tracing.md`.

The corruption scheme is a design decision with the same status as the ablation
method — it defines what "the task" is. Document it as carefully.

Known trap: interpretability illusions for subspace activation patching
(Makelov, Lange & Nanda) — patching into a subspace can produce apparently
causal results via a path that isn't the one you think. Relevant if the project
ever moves from whole components to directions.

### Attribution patching

A gradient-based linear approximation of activation patching that lets you scan
every component at once cheaply. This is how a full-model scan becomes feasible
rather than combinatorial. It is an approximation — use it to *find* candidates,
then verify the candidates with real patching.

### Causal scrubbing / faithfulness metrics

Formal tests of whether a claimed circuit explains the behaviour. Given the
faithfulness-robustness result above, treat any single faithfulness number as a
methodology-dependent quantity, not a property of the circuit. Report the
methodology with the number, always.

## Default metrics

- **Logit difference** as the default. Loss aggregates over the whole
  vocabulary and dilutes the signal for targeted tasks.
- **Loss increase** only where there's a written reason (e.g. broad
  language-modelling degradation, where the whole distribution is the point).
- **Direct effect** decomposition where the question is about a component's
  contribution to the logits specifically.

### Metric definitions

**Notation.** $M$ is the full model; $x$ a clean prompt, $x'$ its paired
corrupt prompt. $M(x)$ is the logit vector at the final position,
$\mathrm{logit}_t(x)$ the logit for token $t$, and
$P_t(x) = \mathrm{softmax}(M(x))_t$. $M(x \mid \operatorname{do}(a = \tilde a))$
is the model run on $x$ with internal activation $a$ overwritten by
$\tilde a$ — Miller et al.'s ablation equation, of which every intervention
below is an instance. $C(x)$ is $M$ with every component outside a set $C$
knocked out. A per-prompt metric is $f(x)$; a dataset-level number is its
mean $F = \mathbb{E}_x[f(x)]$ over a stated distribution of stated size $N$.

#### Per-prompt metrics

- **Logit difference** (the default). For a named correct token $c$ and a
  named competitor $s$:

  $$f_{\mathrm{LD}}(x) = \mathrm{logit}_c(x) - \mathrm{logit}_s(x)$$

  Positive means $c$ is preferred over $s$. IOI uses $c = \mathrm{IO}$,
  $s = \mathrm{S}$; clean mean 3.56 over 100,000 prompts [wang-2022 §2]. It
  answers only "how strongly is $c$ preferred over *this* competitor" —
  nothing about top-1, nothing about the rest of the vocabulary. The
  competitor is a design choice and is part of the metric's name. Wiki:
  `wiki/methods/logit-difference.md`.
- **Correct-token probability.** $f_P(x) = P_c(x)$. ROME's metric and Wang
  et al.'s companion statistic. Bounded, and involves the whole softmax: a
  change can come from the competitor or from anywhere else in the
  vocabulary.
- **Top-1 accuracy.** $f_{\mathrm{acc}}(x) = \mathbb{1}[\arg\max M(x) = c]$.
  Reported alongside, never instead. Wang et al.'s "IO over S" is the
  pairwise version $\mathbb{1}[\mathrm{logit}_c(x) > \mathrm{logit}_s(x)]$
  (99.3% clean).
- **Loss.** $f_{\mathrm{loss}}(x) = -\log P_c(x)$ for a single target, or
  mean next-token cross-entropy over a sequence for language-modelling
  degradation. Only with a written reason.
- **Per-head logit contribution** (an attribution, not a model metric).
  For head output $h_i(x)$ at the final position and unembedding column
  $W_U[t]$:

  $$\langle h_i(x),\, W_U[c] \rangle - \langle h_i(x),\, W_U[s] \rangle$$

  Skips the final LayerNorm scaling [wang-2022 §3.1 fn. 1]. Licenses a
  claim about what the head writes toward the two tokens, not about its
  effect after the LayerNorm.

#### Effect sizes under an intervention

All differences of the same $F$ under two conditions. Which $F$ is stated
every time.

- **Ablation effect, total** (an E3 heatmap cell). For component $a$ and
  ablation value $\tilde a$ — zero, mean over a reference set of stated
  size, or resample from $x'$:

  $$\Delta_{\mathrm{total}}(a) = F(M) - \mathbb{E}_x\big[\, f\big(M(x \mid \operatorname{do}(a = \tilde a))\big) \big]$$

  Positive means the ablation hurt. Necessity only. Everything downstream
  responds, backup heads included, so the number *contains* compensation.
- **Direct effect, this project's sense** (O-011 resolution). Same
  substitution, but every other attention head's output is held at its
  clean value, so the change reaches the final residual state through $a$'s
  own write and not through any later head. Under the `wang` convention,
  the harness default and the one E2 and E3 use, MLPs are part of the
  direct path and recompute [miller-2024 App. F], and the final LayerNorm
  recomputes as well. So the number also contains what later MLPs and the
  final LayerNorm do in response to $a$. Under `term`, MLPs are held too.
  Wang et al. implement it as path patching with the
  receiver set to the residual end state [wang-2022 App. B fn. 3]; Miller
  et al. call it edge ablation to the logits.

  $$\Delta_{\mathrm{direct}}(a) = F(M) - \mathbb{E}_x\big[\, f\big(M(x \mid \tilde a \text{ on the edge } a \to \mathrm{logits} \text{ only})\big) \big]$$

  $\Delta_{\mathrm{total}} - \Delta_{\mathrm{direct}}$ is the net effect
  of every route through later heads. It contains downstream compensation
  but is not equal to it: $a$'s own indirect effect through later heads
  (an earlier head that acts by changing what a later head attends to) is
  in the same difference, often with the opposite sign. Under `wang`,
  compensation by later MLPs or by the final LayerNorm sits inside
  $\Delta_{\mathrm{direct}}$ and is not in the difference at all. It is the
  E4 baseline E3 records for free, read as a net figure. **Name
  collision:** Meng et al.'s "direct effect" (fn. 3) is Pearl's mediation
  quantity — the corruption's effect that bypasses a restored state — and
  is not this.
- **Pattern-preserving ablation effect.** As total, but downstream
  attention patterns are replayed from the clean run. The third value of
  the one path-restriction setting (O-011).
- **Causal tracing effects** (ROME; restore direction). With $P$, $P^*$,
  $P^*_h$ the correct-object probability under the clean run, the
  corrupted run, and the corrupted run with state $h$ restored to clean:

  $$\mathrm{TE} = P - P^*, \qquad \mathrm{IE}(h) = P^*_h - P^*$$

  $\mathrm{ATE}$ and $\mathrm{AIE}(h)$ are the same, averaged over prompts.
  $\mathrm{IE}(h)$ licenses *sufficiency of $h$ given that corruption*,
  not necessity [meng-2022 §2.1]. Wiki: `wiki/methods/causal-tracing.md`.

#### Circuit-level scores

Computed from $F(C) = \mathbb{E}_x[\, f(C(x)) \,]$ under one knockout
method on one reference distribution — Wang et al.: mean ablation on
$p_{\mathrm{ABC}}$, per (head, position). Change the knockout and every
score changes. Wiki: `wiki/methods/circuit-validation-criteria.md`.

- **Faithfulness, absolute.** $|F(M) - F(C)|$, small is good. Wang et al.:
  0.46 against $F(M) = 3.56$ [wang-2022 §4].
- **Faithfulness, ratio** (Miller et al.'s "logit difference recovered"):

  $$\mathrm{faithfulness} = \frac{F(C)}{F(M)} \times 100\%$$

  100% = the circuit alone matches the full model; above 100% = it prefers
  the correct token *more*; negative = the competitor wins. Wang et al.:
  87%. **Averaging order is part of the definition:**
  $\mathbb{E}_x[f(C(x))] \,/\, \mathbb{E}_x[f(M(x))]$ is Wang et al.'s
  number; $\mathbb{E}_x[\, f(C(x)) / f(M(x)) \,]$ is systematically higher
  and explodes on prompts whose denominator is near zero (IQR up to 50
  points on IOI) [miller-2024 §4.1–4.2]. E1 reports both and the
  per-prompt spread.
- **Incompleteness score**, for $K \subseteq C$:

  $$\big|\, F(C \setminus K) - F(M \setminus K) \,\big|$$

  Large means $M$ has something outside $C$ that fills in for $K$. Only
  ever searched, never proven small; the search strategy decides the
  answer [wang-2022 §4.1].
- **Minimality score**, for $v \in C$ and a chosen context
  $K \subseteq C \setminus \{v\}$:

  $$\big|\, F\big(C \setminus (K \cup \{v\})\big) - F(C \setminus K) \,\big|$$

  Large means $v$ matters in that context. A *conditional* necessity
  claim; $K$ is part of the statement [wang-2022 §4.2].

#### Phase-specific

- **In-context learning score** (Olsson et al.; E2, E6):

  $$\mathrm{ICL} = \ell_{500} - \overline{\ell_{50}}$$

  the loss at token 500 minus the mean loss at token 50, over 10,000 fixed
  512-token examples [olsson-2022 §Data Collection]. A gap between two
  losses, so damage that worsens early-context prediction *raises* it. Fix
  the sign in code and state it next to every number. Wiki:
  `wiki/concepts/in-context-learning.md`.

#### What every metric statement carries

Rule 1 phrasing covers all of the above: "under {ablation value, path
restriction, direction} on {dataset, size $N$, corruption scheme},
{intervention on $a$} changes {metric, with its two named tokens where
applicable} by {amount}; seed; model revision hash." Per battery item, two
more fields (O-009 addendum): the **expected direction** of the metric
under damage, and the **mean-ablation reference size** next to every
mean-ablation number (rule 4).

## The through-line for any writeup

"Importance" is not one quantity. Correlational knockout, causal patching, and
faithfulness-verified circuits are three increasingly demanding questions, and
zero- vs mean-ablation splits the first one into two different questions again.
Being explicit about which is being measured is most of the work.
