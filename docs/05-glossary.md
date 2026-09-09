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
