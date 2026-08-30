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
