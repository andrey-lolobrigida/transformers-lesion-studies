# 01 — Methods: what each measurement actually licenses

This is the most important reference document in the project. The
methodological content is easy; the discipline about what each method entitles
you to claim is the hard part, and it's where the project's credibility lives.

## The core distinction

**Ablation tests necessity.** Remove the component, see if behaviour breaks.
Answers: "does the model need this?"

**Activation patching tests sufficiency.** Take a run on a corrupted input,
patch in clean activations from one component, see if correct behaviour is
restored. Answers: "is this enough to produce the behaviour?"

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

They also found faithfulness scores drift with the number of prompts used to
compute the mean — small samples (single-digit prompt counts) can reproduce
headline figures for the wrong reason, because noisy means push the model
toward specific wrong answers rather than merely destroying information.

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
activations back in, one component at a time, and measure how much correct
behaviour is restored. This isolates causal contribution rather than
correlational importance, and it's what phase E2 uses to verify the
reproduction.

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

## The through-line for any writeup

"Importance" is not one quantity. Correlational knockout, causal patching, and
faithfulness-verified circuits are three increasingly demanding questions, and
zero- vs mean-ablation splits the first one into two different questions again.
Being explicit about which is being measured is most of the work.
