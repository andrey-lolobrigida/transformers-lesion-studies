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

**Direct effect** — a component's contribution to the output logits via the
residual stream, without going through later components.

**Diaschisis** — borrowed from neuroscience: disruption of a component caused by
damage elsewhere that fed into it, rather than by damage to the component
itself. The confound that makes lesion mapping hard.

**Logit difference** — the difference in logits between a correct and an
incorrect candidate token. The default metric here, preferred over loss for
targeted tasks.

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
`A = softmax*(tᵀ · C_QK · t)`. Expands into one term per path from tokens to
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

**Smeared key** — an architectural variant with a trainable per-head `α` that
interpolates each key with the previous position's key,
`k_j = σ(α)k_j + (1−σ(α))k_{j−1}`, making induction expressible in one layer.
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
distance, `W_in^{later} W_out^{earlier}`, obtained by multiplying their weights
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
input/output cosine similarity, or heads with large negative `W_OV` eigenvalues
attending to the present token. Stated as a hint, not a finding.

**Half-linear** — the paper's description of an attention head: given the
attention pattern, the head is linear; only the softmax producing the pattern
is not.

**`W_QK`** — `W_Q^T W_K`, a `d_model × d_model` bilinear form of rank ≤
`d_head`; `x_dest^T W_QK x_src` is the attention score. The matrix form of the
QK circuit. (TransformerLens writes the same object with transposed factors;
check at E0.)

**`W_OV`** — `W_O W_V`, a `d_model × d_model` linear map of rank ≤ `d_head`;
what a head adds to the destination per unit of attention to a source. The
matrix form of the OV circuit. Its right singular vectors are the subspace
read, its left singular vectors the subspace written.

**`A ⊗ W_OV`** — a head's action as a tensor product: `A` mixes across
positions, `W_OV` acts on each token's vector; `h(x) = (A ⊗ W_OV) x`.

**Freezing attention patterns (trick)** — run once to record every pattern,
run again with patterns forced to the recorded values; the model is then a
linear function of the tokens. Origin of pattern-preserving ablation.

**Path expansion** — multiplying out the product of layers, with patterns
frozen, into a sum of end-to-end paths from tokens to logits. Wiki:
`methods/path-expansion.md`.

**Direct path (refined)** — the `W_U W_E` term of the path expansion: the
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

**Same-matching matrix** — the QK analogue: a matrix `W` in a composed QK term
that scores highest when query-side and key-side tokens agree. Also
summarised by positive eigenvalues.

**Eigenvalue copying statistic** — positivity of the eigenvalues of
`W_U W_OV W_E` (or of a QK `W`) as a data-free summary of copying / matching.
Evidence, not proof. Wiki: `methods/weight-statistics.md`.

**V-composition** — a head's value matrix reading a subspace written by an
earlier head; unlike Q/K-composition it does not change any attention pattern
and instead creates a virtual attention head. (Completes the Q- and
K-composition entries of 2026-09-08.)

**Virtual attention head** — the V-composition of two heads, behaving as one
head with pattern `A² A¹` and OV matrix `W_OV² W_OV¹`. Their number grows
quadratically with depth. Small effect in the paper's two-layer model.

**Composition score** — normalised Frobenius norm of the virtual weight between
two heads (`‖W_QK² W_OV¹‖_F / (‖W_QK²‖_F ‖W_OV¹‖_F)` for K), minus the
random-matrix baseline. The paper's own figure of these was affected by a bug
and later corrected.

**Term-importance ablation** — with all patterns frozen, replace head outputs
by zero, then by previously saved outputs, one path order at a time, and
difference the losses to get the marginal contribution of nth-order paths.
Targets V-composition only.

**Value-weighted attention pattern** — the attention weight scaled by the norm
of the value vector at the source, `A_{ij} ‖v_j‖`; corrects for heads that park
on a default token with a near-zero value vector.

**Pointer arithmetic (positional)** — an induction mechanism available only
when positional embeddings live in the residual stream: one head fetches the
positional embedding of an earlier copy of the current token; a second head's
query, via Q-composition, shifts it forward one position. Reported in "at
least one case in GPT-2", size unspecified.
