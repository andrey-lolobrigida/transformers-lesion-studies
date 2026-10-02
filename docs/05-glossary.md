# 05 — Glossary

Terms as used in this project. Where a term has a looser common usage, the
stricter version here is the one that applies in results docs.

**Ablation** — deliberately disabling a component to measure whether behaviour
depends on it. Tests *necessity*.

**Zero-ablation** — ablation by replacing the component's output with zero.
Removes both the information the component carried and its baseline
contribution to the residual stream. Moves the model off-distribution.

**Mean-ablation** — ablation by replacing the component's output with its
average over a dataset. Removes input-dependent information while preserving
the average contribution. The dataset size matters and is always logged.

**Resample ablation** — ablation by replacing the component's output with its
output on a different input from the same distribution. A third way of staying
in-distribution.

**Activation patching** — copying activations from a clean run into a corrupted
run (or vice versa) to isolate causal contribution. Tests *sufficiency*.

**Causal tracing** — activation patching applied to locate where a piece of
information lives; the ROME formulation.

**Attribution patching** — gradient-based linear approximation of activation
patching, cheap enough to scan every component. An approximation: used to
generate candidates, not to confirm them.

**Circuit** — a subgraph of components that together implement a behaviour.
Note that which subgraph counts depends partly on the ablation methodology used
to isolate it. Olah et al. 2020 define it *structurally* rather than
behaviourally — nodes are neurons or directions, edges are the weights between
them — which is a different object; see `wiki/concepts/circuit.md`.

**Faithfulness** — the degree to which a proposed circuit reproduces the full
model's behaviour on a task. Not a property of the circuit alone; it depends on
the ablation methodology, and should always be reported alongside it.

**Causal scrubbing** — a formal methodology for testing whether a claimed
circuit actually explains a behaviour rather than merely correlating with it.

**Induction head** — an attention head implementing in-context copying: given
`… A B … A`, it promotes `B`.

**Backup head** — a head that contributes little under normal operation but
increases its contribution when a primary head is ablated. Learned redundancy,
as distinct from the mechanical compensation below.

**Self-repair** — the general phenomenon of a model partially recovering
behaviour after a component is ablated. Has at least two distinct sources that
this project keeps separate:

- **Mechanical self-repair** — LayerNorm rescaling. Removing an additive
  contribution reduces the residual stream's norm, so LayerNorm divides by a
  smaller factor and amplifies everything remaining. Happens regardless of what
  the removed component computed. Not learned, not adaptive.
- **Compensatory self-repair** — backup heads and MLP adjustments that respond
  to the specific ablation. The part that is actually interesting.

**Hydra effect** — self-repair at the layer level: ablate one attention layer, a
later layer takes over part of its function.

**Direct effect** — in this project, a component's contribution to the logits
measured by *edge ablation with the receiver set to the logits*
(`component_type="edge"`, `receiver=Logits()` in the E1a harness). The MLP
convention is part of the definition and every such number carries
`direct_effect_definition: "wang"` (MLPs on the path recompute; Wang et al.'s
path patching) or `"term"` (MLPs held at their unintervened values; the
component's own additive term). Neither is Meng et al.'s mediation-sense
direct effect, which shares the name and nothing else (O-011, 2026-09-20
addendum; see the two entries below).

**Diaschisis** — borrowed from neuroscience: disruption of a component caused by
damage elsewhere that fed into it, rather than by damage to the component
itself. The confound that makes lesion mapping hard.

**Logit difference** (`ld` in artifacts and code) — the difference in logits
between a correct and an incorrect candidate token. The default metric here,
preferred over loss for targeted tasks. Result artifacts and `src/lesion/`
abbreviate it `ld` throughout — `results.clean.mean_ld`,
`results.ablated.mean_ld`, `sem_ld`, `results.effect.ld` — so a results table
reading `ablated mean ld` means the mean logit difference left after the
ablation. On IOI that is `logit(IO) − logit(S)` at the END position.

**Superposition** — networks representing more features than they have neurons,
making individual neurons polysemantic. Named in Olah et al. 2020 from a car
feature deliberately spread across dog-detector neurons; the geometric reason is
that a space of dimension *n* holds only *n* orthogonal vectors but
exponentially many almost-orthogonal ones.

**SAE (sparse autoencoder)** — learns a sparser, more monosemantic feature basis
for a layer's activations. Deferred in this project (D-003).

**Transcoder** — like an SAE but maps a layer's input to its output, making it
usable for tracing computation across layers rather than reading off a single
layer.

---

## Added 2026-08-30 — R0 extraction, Olah et al. "Zoom In" (`olah-2020`)

Vision-model vocabulary, kept because the framing transfers even where the
substrate does not. Wiki pages under `wiki/concepts/` carry the detail.

**Feature** — a scalar function of the input; in practice a direction in a
layer's activation space, often a single neuron. The claim that these are
individually meaningful is the first of Zoom In's three speculative claims.

**Direction** — a linear combination of neurons in a layer; a vector in that
layer's representation space. An individual neuron is the special case of a
basis direction. Features are directions first and neurons only incidentally.

**Meaningful feature** — a feature that genuinely responds to an articulable
property of the input. May still be noisy or imperfect.

**Pure feature** — responds to a single latent variable. Contrast polysemantic.

**Polysemantic feature** — responds to multiple *unrelated* latent variables;
the InceptionV1 neuron firing for cat faces, car fronts and cat legs. Not merely
"responds to several things".

**Multifaceted feature** — responds to several cases that genuinely belong
together, such as a dog head facing left or right. Distinguished from
polysemantic, where the cases are unrelated. The distinction is easy to lose and
is what makes a naming claim defensible or not.

**Family** — a set of features in one layer detecting small variations of the
same thing, such as curve detectors jointly tiling all orientations.

**Client feature** — a later-layer feature that relies on a particular earlier
one. A circle detector is a client of curve detectors.

**Upstream / downstream** — in an earlier layer / in a later layer.

**Circuit motif** — a recurring abstract pattern across circuits, borrowed from
systems biology. Zoom In names three: equivariance, unioning over cases, and
superposition.

**Equivariance** — the symmetry of a problem appearing as a symmetry in the
weights; the weights of a curve-detector circuit rotate with the orientation of
the detector.

**Unioning over cases** — a network detecting two cases separately, with the
pathways inhibiting each other, then combining them into an invariant unit.
Gives the circuit XOR-like properties rather than merely OR-like ones.

**Universality** — the hypothesis that analogous features and circuits form
across models and tasks. Also called *convergent learning*. Zoom In's third
claim, and the one its authors say rests on anecdote.

**Feature visualization** — optimising an input to maximally activate a unit, to
see what it responds to. Establishes a causal link, since everything in the
resulting image was added to raise the activation. A vision technique with no
clean equivalent for discrete tokens.

---

## Added 2026-09-08 — R0 extraction, Olsson et al. "In-context Learning and Induction Heads" (`olsson-2022`)

**In-context learning** — a model predicting later tokens better than earlier
ones, as context accumulates. Two incompatible conceptions exist: few-shot task
performance (Brown et al.) and loss-versus-token-index (Kaplan et al.). This
project uses the second when reproducing Olsson et al., and says which one it
means every other time.

**In-context learning score** — the loss of the 500th token minus the average
loss of the 50th token, over a 512-token context, averaged over examples. Note
it is a *difference*, so damaging early-context prediction raises it; and note
that as literally defined it is negative when the model is doing in-context
learning, while the paper reports positive nats. Fix the sign in code and state
it.

**Prefix matching** — a head property: on a repeated random sequence, the head
attends back to tokens that were *followed by* the current token. A QK-circuit
property. (The published definition was corrected on 2022-09-20; the original
wording said "preceded by" and is an erratum.)

**Copying (head property)** — the head's direct-path output raises the logit of
the token it attends to. An OV-circuit property. Prefix matching plus copying is
Olsson et al.'s working definition of an induction head.

**Previous-token head** — a head that attends from token *i* to token *i−1*,
shifting information back one position. The earlier half of the two-head
induction circuit; not itself an induction head.

**Head activation evaluator** — a cheap behavioural score for a head computed
from activations on synthetic sequences rather than from weights. Olsson et al.
define three: copying, prefix matching, previous-token attention. Averaged over
10 examples in the source, which is small enough that the sample size belongs
next to any number derived from them.

**Phase change (induction bump)** — the narrow early-training window in which
in-context learning appears, induction heads form, the loss curve bends, and the
per-token-loss trajectory pivots. Reported at roughly 2.5–5e9 tokens; the paper
gives 1–3e9 for its small models in a different section.

**Full ablation** — ablation in which the removal propagates everywhere,
including into later heads' queries and keys, so attention patterns change.

**Pattern-preserving ablation** — ablation in which all attention patterns are
frozen to their clean-run values, so only downstream value computations are
affected. An axis independent of what value is substituted (zero, mean,
resample). With patterns frozen a head's action is linear, which in an
attention-only model makes the ablation exactly equivalent to subtracting that
head's terms from the logits — an equivalence that does **not** survive MLPs.

**QK circuit** — the part of a head that computes *where it attends*:
$A = \operatorname{softmax}^*(t^\top \cdot C_{QK} \cdot t)$. Expands into one term per path from tokens to
attention scores.

**OV circuit** — the part of a head that computes *what it writes* to the
residual stream given where it attended. Copying is characterised by positive
OV eigenvalues.

**K-composition** — a head's key matrix reading from a subspace written by an
earlier head. The standard induction mechanism: K-composition with a
previous-token head.

**Q-composition** — the same on the query side. Reportedly the route GPT-2 uses
for a positional "pointer arithmetic" induction mechanism, which matters because
this project's model is GPT-2 small.

**Direct path** — the route from a component straight to the unembedding without
passing through later components. Copying scores are measured on it, which is
why a head whose output is further processed by later layers can score low while
still contributing.

**Per-token loss vector** — the vector of log-likelihoods a model assigns to a
fixed sampled set of tokens, treated as a point in "function space" so that
different models and checkpoints can be compared regardless of their weights.
PCA over these is how Olsson et al. plot training trajectories.

**Smeared key** — an architectural variant with a trainable per-head $\alpha$ that
interpolates each key with the previous position's key,
$k_j = \sigma(\alpha)\, k_j + (1 - \sigma(\alpha))\, k_{j-1}$, making induction expressible in one layer.
Used as an interventional test, not a proposal.

---

## Added 2026-09-14 — R0 extraction, Elhage et al. "A Mathematical Framework for Transformer Circuits" (`elhage-2021`)

**Attention-only transformer** — a transformer with the MLP layers removed;
the paper's object of study for zero, one and two layers. Its results are exact
there and heuristic once MLPs are present.

**Residual stream** — the per-token vector every layer reads from linearly and
writes to by addition; the sum of the embedding and all layer outputs so far.
Preferred over "embedding" because subspaces of it hold information about
*other* tokens. Wiki: `concepts/residual-stream.md`.

**Virtual weight** — the implicit connection between two components at any
distance, $W_{\text{in}}^{\text{later}} W_{\text{out}}^{\text{earlier}}$, obtained by multiplying their weights
through the residual stream. The transformer analogue of an edge in a circuit.

**Privileged basis** — an activation has one when the architecture pushes
features to align with basis directions (e.g. a ReLU). Tokens, attention
patterns and MLP activations have one; the residual stream, keys, queries and
values do not, so their individual dimensions are not meaningful.

**Bottleneck activation** — a lower-dimensional intermediate between two
higher-dimensional activations, e.g. the residual stream between MLP layers or
a value vector between two token positions. Expected to be hard to interpret
directly.

**Memory management (head or neuron)** — speculated role of components that
delete information from the stream: MLP neurons with strongly negative
input/output cosine similarity, or heads with large negative $W_{OV}$ eigenvalues
attending to the present token. Stated as a hint, not a finding.

**Half-linear** — the paper's description of an attention head: given the
attention pattern, the head is linear; only the softmax producing the pattern
is not.

**$W_{QK}$** — $W_Q^\top W_K$, a $d_{\text{model}} \times d_{\text{model}}$ bilinear form of
rank $\le d_{\text{head}}$; $x_{\text{dest}}^\top W_{QK}\, x_{\text{src}}$ is the attention score. The matrix form of the
QK circuit. (TransformerLens writes the same object with transposed factors;
check at E0.)

**$W_{OV}$** — $W_O W_V$, a $d_{\text{model}} \times d_{\text{model}}$ linear map of rank $\le d_{\text{head}}$;
what a head adds to the destination per unit of attention to a source. The
matrix form of the OV circuit. Its right singular vectors are the subspace
read, its left singular vectors the subspace written.

**$A \otimes W_{OV}$** — a head's action as a tensor product: $A$ mixes across
positions, $W_{OV}$ acts on each token's vector; $h(x) = (A \otimes W_{OV})\, x$.

**Freezing attention patterns (trick)** — run once to record every pattern,
run again with patterns forced to the recorded values; the model is then a
linear function of the tokens. Origin of pattern-preserving ablation.

**Path expansion** — multiplying out the product of layers, with patterns
frozen, into a sum of end-to-end paths from tokens to logits. Wiki:
`methods/path-expansion.md`.

**Direct path (refined)** — the $W_U W_E$ term of the path expansion: the
route from embedding to unembedding through no layer. Can only encode bigram
statistics; in a zero-layer model it is the whole model. (Extends the
2026-09-08 entry, which used "direct path" for a component's route straight to
the unembedding; both senses are "no further processing between here and the
logits".)

**Skip-trigram** — a pattern `[source] … [destination] → [output]` that a
one-layer head implements: the QK circuit attends from destination to source,
the OV circuit moves the output logit. One-layer attention-only models are an
ensemble of a bigram model and skip-trigram models.

**Skip-trigram "bug"** — because a head stores the trigram in factored form
(QK knows source–destination, OV knows source–output), it cannot avoid also
boosting the cross-combinations, e.g. `keep … in → bay`.

**Copying matrix** — an OV circuit that maps tokens toward themselves, so
attending to a token raises that token's logit. Summarised by positive
eigenvalues; not a settled formalisation.

**Same-matching matrix** — the QK analogue: a matrix $W$ in a composed QK term
that scores highest when query-side and key-side tokens agree. Also
summarised by positive eigenvalues.

**Eigenvalue copying statistic** — positivity of the eigenvalues of
$W_U W_{OV} W_E$ (or of a QK $W$) as a data-free summary of copying / matching.
Evidence, not proof. Wiki: `methods/weight-statistics.md`.

**V-composition** — a head's value matrix reading a subspace written by an
earlier head; unlike Q/K-composition it does not change any attention pattern
and instead creates a virtual attention head. (Completes the Q- and
K-composition entries of 2026-09-08.)

**Virtual attention head** — the V-composition of two heads, behaving as one
head with pattern $A^2 A^1$ and OV matrix $W_{OV}^2 W_{OV}^1$. Their number grows
quadratically with depth. Small effect in the paper's two-layer model.

**Composition score** — normalised Frobenius norm of the virtual weight between
two heads ($\lVert W_{QK}^2 W_{OV}^1 \rVert_F / (\lVert W_{QK}^2 \rVert_F\, \lVert W_{OV}^1 \rVert_F)$ for K), minus the
random-matrix baseline. The paper's own figure of these was affected by a bug
and later corrected.

**Term-importance ablation** — with all patterns frozen, replace head outputs
by zero, then by previously saved outputs, one path order at a time, and
difference the losses to get the marginal contribution of nth-order paths.
Targets V-composition only.

**Value-weighted attention pattern** — the attention weight scaled by the norm
of the value vector at the source, $A_{ij} \lVert v_j \rVert$; corrects for heads that park
on a default token with a near-zero value vector.

**Pointer arithmetic (positional)** — an induction mechanism available only
when positional embeddings live in the residual stream: one head fetches the
positional embedding of an earlier copy of the current token; a second head's
query, via Q-composition, shifts it forward one position. Reported in "at
least one case in GPT-2", size unspecified.

---

## Added 2026-09-19 — R1 extraction, Wang et al. "Interpretability in the Wild" (`wang-2022`)

**IOI (indirect object identification)** — the task: given "When Mary and
John went to the store, John gave a drink to", predict "Mary". A dependent
clause introduces the indirect object (IO) and the subject (S); the main
clause repeats S. Wiki: `concepts/ioi-circuit.md`.

**S1, S2, IO, END** — position labels in an IOI sentence: first and second
occurrence of the subject, the indirect object, and the final token position
where the prediction is made. **S1+1** is the token after S1.

**`p_IOI`** — the distribution over IOI sentences generated from 15 templates,
100 single-token names and 20 places / objects, in both ABBA and BABA orders.

**`p_ABC`** — the same templates with three unrelated random names, so no
name is duplicated and there is no single plausible IO. Wang et al.'s
reference distribution for mean ablation and the corrupted input for path
patching.

**Knockout** — Wang et al.'s word for removing a set of nodes from the
computational graph while keeping all other computation. Implemented by
ablation; the paper's is mean ablation.

**Reference distribution (mean ablation)** — the dataset over which the
replacement mean is computed. It decides what information the ablation
removes: only what *varies* across the reference. Wiki:
`methods/mean-ablation.md`.

**Template-matched mean** — a mean computed across samples of one template
only, so that the grammatical role at each position is the same in every
sample averaged.

**Node, (head, position) pair** — the unit Wang et al. knock out: one head at
one token position, not a head at all positions. GPT-2 small's IOI circuit is
26 such nodes, "1.1% of the total number of (head, token position) pairs".

**Behavioural circuit** — Wang et al.'s definition: a subgraph $C$ of the
model's computational graph whose function $C(x)$ is the model's output with
everything outside $C$ knocked out. The knockout method is part of the
definition. Contrast the structural definition of Olah et al. (2020 entry);
reconciliation proposed on `wiki/concepts/circuit.md`.

**Path patching** — run on a clean input, but along the paths from one
*sender* head to a set of *receivers* (through residual connections and
MLPs, not through other heads) use the sender's activation from a corrupted
input. Other heads' outputs are frozen to clean values. Measures the
necessity of that route. Wiki: `methods/path-patching.md`.

**Sender / receiver** — in path patching, the head whose activation is
replaced and the set of nodes (a head's Q, K or V input, or the final
residual state) that receive the replaced signal.

**Freezing (activations)** — Wang et al.'s sense: during a forward pass with
some earlier edit, hold an activation at the value it had on the *unedited*
run of the same input. Distinct from the 2026-09-14 entry *freezing
attention patterns*: that pins patterns and lets outputs respond; this pins
head outputs and lets MLPs respond.

**Direct effect (Wang et al.'s operationalisation)** — path patching with the
receiver set to the final residual state: every path from the head to the
logits that avoids other heads, MLPs included. Differs from the "head's own
term" sense in the O-011 resolution; see O-011 addendum.

**Indirect effect** — a head's influence on the metric that is mediated by
other heads; in Wang et al. recovered edge by edge by tracing backwards, or
measured in total by a knockout.

**Patching direction** — which run receives the patch. Corrupted activation
into a clean run (Wang et al.) asks necessity; clean activation into a
corrupted run asks sufficiency. The 2026-08 entry "activation patching …
tests sufficiency" is true of the second direction only. (The words
*noising* and *denoising* for the two directions are common usage, not this
paper's.)

**Activation patching (refined)** — Wang et al.'s use: replace the *outputs*
of a set of heads with their outputs on a counterfactual input and recompute
the whole forward pass, nothing frozen. Coarser than path patching about
routes; able to see within-class interactions path patching holds fixed.

**Counterfactual dataset (signal-specific)** — a transformed copy of `p_IOI`
built so that patching from it moves exactly one signal: random-name flip
(token signal uncorrelated), IO ↔ S1 flip (position inverted), IO ← S2
replacement (both inverted), and their compositions.

**Token signal / position signal** — the two components of the S-Inhibition
heads' output: the identity of S, and the position of S1. Position weighs
more (≈ 2.31 vs 0.99 in logit-difference units) and appears to be relative
(S1 to S2), not absolute.

**Pointer (communication by)** — heads "sharing the location of a piece of
information instead of copying it": the position signal is a pointer to S1.

**Faithfulness (Wang et al.'s definition)** — $\lvert F(M) - F(C) \rvert$, the gap
between the model's and the circuit's mean logit difference, with $F$
computed under the knockout that defines $C$. IOI circuit: 0.46 (13%), i.e.
87% retained. Extends the 2026-08 entry with its source.

**Completeness / incompleteness score** — for a subset $K \subseteq C$,
$\lvert F(C \setminus K) - F(M \setminus K) \rvert$; a circuit is complete if this is small for every
$K$. Only ever searched (random, class-wise, greedy), never proven. Greedy
search found 3.09 (87% of baseline) on the IOI circuit.

**Minimality / minimality score** — for a node $v$, the largest
$\lvert F(C \setminus (K \cup \{v\})) - F(C \setminus K) \rvert$ over some $K \subseteq C \setminus \{v\}$; every node should
have one that is non-trivial. A conditional necessity claim: $K$ is part of
the statement.

**Naïve circuit** — Wang et al.'s baseline: the main head classes without
Backup or Negative Name Movers. As faithful as the full circuit; more easily
shown incomplete.

**Greedy completeness search** — Algorithm 3: repeatedly sample $k$ nodes
from $C \setminus K$, add the one that moves the incompleteness score most.

**Name Mover** — a head active at END that attends to a name and copies it
to the logits (9.6, 9.9, 10.0). **Negative Name Mover** — same, writing
against the attended name (10.7, 11.10). **Backup Name Mover** — one of
eight heads with small effect in the intact model that become the main direct
contributors when the Name Movers are knocked out. Cause "still unclear";
dropout during training is the authors' conjecture. Refines the 2026-08
*backup head* entry, whose "learned redundancy" is not established by this
source.

**S-Inhibition head** — active at END, attends to S2, writes the token and
position signals into the Name Movers' queries so they avoid S1 and S2
(7.3, 7.9, 8.6, 8.10).

**Duplicate Token head** — active at S2, attends to S1, signals that the
token is a duplicate by writing its position (0.1, 3.0; "fuzzy" 0.10).

**Fuzzy head** — a head whose attention pattern fits a class only weakly or
diffusely (fuzzy Duplicate Token 0.10; fuzzy Induction 5.8, 5.9).

**Copy score** — proportion of samples in which a name is among the top five
logits after pushing the residual stream at that name (after MLP0) through
the head's $W_{OV}$, then $W_U$ and the final LayerNorm. **Negative copy score**
uses $-W_{OV}$. Name Movers > 95%; average head < 20%.

**Induction score / duplicate score / previous token score (Wang et al.'s
variants)** — attention-pattern averages on 100-token random sequences
duplicated once: attention from $T_i$ to $T_{i-99}$, to $T_{i-100}$, and to
$i-1$ respectively. Rankings published, not values.

**IO probability** — the model's probability on the IO token; the paper's
second headline metric (49% on `p_IOI`), alongside logit difference.

**Adversarial example (circuit-derived)** — an IOI sentence with an extra
occurrence of IO, built from the finding that the model relies on duplicate
detection; drops logit difference to 1.23 and makes S win 23.4% of the time.

---

## Added 2026-09-19 — R1 extraction, Miller, Chughtai & Saunders "Transformer Circuit Faithfulness Metrics Are Not Robust" (`miller-2024`)

**Ablation six-tuple** — the six choices that specify a circuit ablation
experiment: granularity, component type, ablation value, token positions,
direction, and set. A faithfulness number without all six is not a
measurement of the circuit. Wiki: `methods/ablation-methodology.md`.

**Granularity** — the level at which the computational graph is drawn:
heads and MLPs (most common; Q, K, V inputs separately), layers, neurons,
subspaces, sparse features.

**Component type (node / edge / branch)** — what is ablated. *Node*: a
component's output, seen by everything downstream. *Edge*: what one
destination receives from one source, in the factorised view. *Branch*: a
whole input-to-output path, in the treeified view; the primitive of causal
scrubbing; exponential in depth.

**Residual / factorised / treeified view** — three equivalent drawings of a
transformer: every component reads the stream; every component has an edge
from every earlier component; every input-to-output path is separated.

**Node patching / edge patching** — node or edge ablation with a cached
activation from another input. Node patching is "vanilla activation
patching".

**Ablation value** — what is written in: zero, Gaussian noise (on the
embeddings; ROME), resample (another input's activation), mean (over a
reference set, with a set-size sub-choice).

**Resample ablation** — replace an activation with its value on a paired
corrupt input. Miller et al. use it interchangeably with *activation
patching*. Keeps the model near-distribution; adds the corrupt prompt's
signal as well as removing the clean one. Wiki: `methods/resample-ablation.md`.

**Token positions (axis)** — ablate at all positions, or only at positions
outside the circuit's specified set. A circuit specified with positions is
tested with positions.

**Ablation direction** — *ablate clean*: clean input, corrupt values
written in (destroys signal; necessity). *Restore clean*: corrupt input,
clean values written in (restores signal; sufficiency). Supersedes the
2026-09-19 Wang-pass entry *patching direction* with the source's names.

**Set (circuit / complement)** — whether the circuit's components or
everything outside them is ablated. Crossed with direction gives four
targets: destroy performance, restore performance, maintain performance,
maintain inefficacy.

**Faithfulness target** — which of those four an experiment measures.
Restore-into-circuit and ablate-complement both compare to the full model
but differ: the first lets clean signal flow outside the circuit.

**Logit difference recovered** — Wang et al.'s faithfulness ratio as Miller
et al. name it: the ablated model's logit difference over the full
model's, ×100. Over 100% is possible. The ratio of means and the mean of
ratios differ substantially.

**Averaging order** — $\mathbb{E}[F]/\mathbb{E}[M]$ (Wang et al.) versus $\mathbb{E}[F/M]$; the second
is higher on IOI and has heavy per-prompt outliers.

**Worst-case faithfulness** — Miller et al.'s recommendation to report the
per-prompt distribution (interquartile range) alongside the mean; the IOI
circuit is faithful on average and not for many prompts.

**Ground-truth circuit (Tracr)** — the edges a compiled model's known
program uses; Miller et al. show it depends on the ablation value, because
input-invariant information (positional encoding) is removed by zero
ablation and kept by resample.

**"The ablation partly determines the task"** — the paper's thesis and the
source of epistemic rule 3. Zero ablation asks for the circuit that
includes deciding *what kind* of output to make; mean asks for the circuit
that completes the task *given* that context.

**Interchange intervention / causal tracing** — other names for activation
patching (App. F).

**AutoCircuit** — the authors' library: edge patching with mean, zero and
resample on TransformerLens models.

## Added 2026-09-20 — R1 skim, Meng et al. "Locating and Editing Factual Associations in GPT" (`meng-2022`)

**Causal tracing** (refined) — activation patching in the *restore*
direction over a (token × layer) grid: corrupt the input, restore one clean
internal state, measure how much of the correct answer's probability
returns. Tests sufficiency given the corruption. Wiki:
`methods/causal-tracing.md`.

**Total effect (TE) / indirect effect (IE)** — TE is the correct-object
probability lost to the corruption; IE of a state is the probability
regained when that one state is restored while the input stays corrupted.
**ATE / AIE** are their averages over the prompt sample (§2.1).

**Direct effect (mediation sense)** — in Meng et al. (fn. 3), the part of
the corruption's effect that bypasses the chosen mediator. Found "noisy and
uninformative". *Not* this project's direct effect, which is a component's
own contribution to the logits (O-011); the two share a name and nothing
else.

**Corruption rule** — Meng et al.'s term for the scheme that makes the
baseline run fail: Gaussian noise on the subject-token embeddings at three
times the embedding standard deviation, ten samples per prompt (App. B.1).
Too little noise gives no total effect to mediate (App. B.4).

**Early site / late site** — the two regions of high AIE on GPT-2 XL:
mid-layer MLP windows at the last subject token, and late-layer attention at
the last token of the prompt (§2.2, Fig. 2).

**Restoration window** — for MLP and attention maps, a run of ten
consecutive layers restored together, plotted at the centre layer, because
single-module restoration was "generally negligible" (App. B.2).

**Known-facts filter** — prompts kept only if the clean model's greedy
generation names the correct object before any other capitalised word; the
text before the object becomes the prompt (App. B.1). The mechanism O-009
proposes for the factual-recall battery item.

**Localized factual association hypothesis** — the paper's claim that a
fact is recalled by mid-layer MLPs at the subject's last token and copied
to the last token by later attention (§2.3). Licensed in the paper by the
weight-editing results of §3, not by the trace alone.

**ROME (Rank-One Model Editing)** — a rank-one update to one mid-layer
MLP's second matrix that writes a new key–value association, treating the
MLP as a linear associative memory (§3.1). A weight intervention; not
extracted beyond the name.

**CounterFact** — the paper's dataset of 21,919 counterfactual edit records
with paraphrase and neighbourhood prompts, used to score generalisation and
specificity of edits (§3.3). Its *known-facts* subset is the tracing prompt
source.

## Added 2026-09-20 — R1 closure, circuit-definition reconciliation (D-010 item 3)

**Circuit, structural** — a subgraph read off the parameters: nodes are
neurons, directions or heads, edges are the weights (or virtual weights)
between them. Olah et al. 2020; Elhage et al. 2021. No task or dataset in
the definition. Wiki: `wiki/concepts/circuit.md`.

**Circuit, behavioural** — a subgraph of components *plus the ablation
six-tuple* under which it is claimed to implement a behaviour. Wang et al.
2022 define it through a knockout; Miller et al. 2024 show the ground
truth itself changes with the ablation value. Every results doc states
which of the two senses a claim is about. The unqualified "circuit" at
the top of this glossary is the behavioural sense.

## Added 2026-09-23 — E1b battery

**Gate (E1b)** — the pre-registered clean-model check every battery item
passes on its default corruption scheme before E3: pairwise accuracy ≥ 0.90,
gap ≥ 1.0 logit, and for factual recall ≥ 300 admitted survivors. Thresholds
are ours and never relaxed after seeing numbers; named extras are not gated.
D-014 item 1; `results/E1b/README.md` §3.

**Pairwise accuracy** — the mean over clean prompts of `1[logit[c] > logit[s]]`
at `END`, i.e. the fraction with positive `ld`. Near-automatic for factual
recall, whose prompts already passed a generation filter. D-014 item 1.

**Gap** — mean clean `ld` minus mean corrupt `ld` under an item's corruption
scheme, reported with its standard error; gated as an absolute value
(≥ 1.0 logit), not a ratio. D-014 items 1–2.

**Fraction removed** — the gap divided by the mean clean `ld`: the share of
the clean logit difference a corruption scheme removes. Reported, not gated;
cited beside every later mean- or resample-ablation number drawn from that
scheme. D-014 item 2; `results/E1b/README.md` §8.

**Noise floor (E1b)** — per component, the larger of the per-prompt standard
error and the standard deviation of the ablation effect across five
mean-reference seeds, measured on a fixed sample of 24 components per item. A
heatmap cell has to clear its component's floor. O-009 resolution;
`results/E1b/README.md` §7.

**Survivor** — a factual-recall prompt that passed the single-token, segmentation,
known-facts and partner filters; it counts toward the gate only in a template
with ≥ 30 survivors ("admitted"). `results/E1b/README.md` §4; D-014 item 3.

## Added 2026-09-24 — E1b agreement item (D-013 fallback)

**Attractor** — in the agreement item's prompts `The {N1} {prep} the {N2}`,
the second noun `N2`: a noun between the subject `N1` and the verb, which may
or may not share the subject's grammatical number. D-013 addendum item 4;
`results/E1b/README.md` §10.

**Congruent / incongruent** — an agreement prompt is congruent when the
attractor `N2` shares the subject `N1`'s number (both singular or both
plural) and incongruent when it does not. Exactly 50/50: prompts are drawn
in blocks of 16 balancing (preposition, congruency, subject number); part of
the template key `{prep}/{congruency}`. D-013 addendum item 4 and
balanced-draw paragraph.

**`number_flip`** — the agreement item's default corruption: `N1` replaced by
its own other-number form (`dog` ↔ `dogs`), everything else kept, so
congruent prompts become incongruent and back. `c` and `s` stay the clean
labels, so the corrupt prompt is built to favour `s` if the model agrees, and
the fraction removed is expected near 2 by design (measured: 2.00 on balanced draws; 1.98 on the first run). Ours. D-013 addendum item 5; `results/E1b/README.md` §10.

**`number_flip_all`** — the agreement item's named extra: `N1` and `N2` both
replaced by their other-number forms, so congruency is kept. Ungated. Ours.
D-013 addendum item 5.

## Added 2026-09-29 — E2 reproduction

**Identity rule** — a published class matches iff every member ranks in the
top $k = \max(\text{class size} + 2,\ \text{the rank the source states})$ of all candidates
under the class's own score and receiver (bottom $k$ for negative classes); a
tie straddling the cut counts as inside. Our ranking, not the source's
selection procedure. D-015 item 3; `src/lesion/e2_reproduce.py`.

**Sign rule** — matches iff the effect has the published sign and
$\lvert \text{effect} \rvert > \max(2 \times \text{sem},\ \text{the item's largest E1b noise floor})$; a published
null matches iff the effect stays inside that bound, which shows only that
nothing was found. D-015 item 4; `src/lesion/e2_reproduce.py`.

**Bracket corner** — one full run at one combination of the settings a source
leaves open; for IOI, {15, 7} templates per order × {≈ 7 per template, 2,000
total} mean-reference prompts. The ≈ 7 corners break D-014's floor of 30 and
are labelled so. D-015 item 5; `results/E2/README.md` Pre-registration.

**Contrast value** — for a bracketed magnitude, a named alternative value
that would change the claim (P2: the summed direct effects over $F(M)$; P3:
1.0). A bracket containing it is `bracketed, uninformative`. D-015 item 5.

**Set knockout** — one intervention over several (head, positions) members
at once, with one value, reference, direction and freeze setting, recorded in
the artifact's `spec.set` block. D-015 item 8; `src/lesion/knockout.py`.

**Complement knockout** — a set knockout applied to every head node *outside*
the named members (heads only, MLPs untouched), used for Wang et al.'s $F(C)$.
D-015 item 8; `src/lesion/knockout.py`.

**Fraction restored** — for a restore-clean run, (mean `ld` with clean
activations written in − mean corrupt `ld`) / (mean clean `ld` − mean corrupt
`ld`): a sufficiency reading, never a necessity one. Can exceed 1 or be
negative. `src/lesion/e2_targets.py`; `results/E2/README.md` I4, P4.
