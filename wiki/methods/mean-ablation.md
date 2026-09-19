---
title: Mean ablation
type: method
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E1
updated: 2026-09-19
---

# Mean ablation

*Drafted from Wang et al., where it is the knockout method behind every
circuit number in the paper. Miller et al. (R1) is the source for its
robustness and for the sample-size effect that epistemic rule 4 encodes.*

## In one sentence

Knock a component out by replacing its output with its **average over a
reference distribution**, so that what varies across that distribution is
removed and what is constant across it is kept.

## Claim-licence block

| | |
|---|---|
| **Answers** | Necessity of the *distribution-varying* information a component carries: "does behaviour break when this component's output is replaced by what it typically outputs on the reference set?" |
| **Does NOT answer** | Necessity of the component's *constant* contribution — that is deliberately preserved (and is what [[zero-ablation]] removes in addition). Sufficiency of anything. |
| **Confounds** | The reference distribution decides what counts as "varying". Wang et al. reject `p_IOI` as the reference because too much task information is constant across it (every sentence has a duplicated name) and use `p_ABC` instead; a different reference is a different experiment. Means are taken *per template and per position* so that grammatical role stays aligned — a mean pooled across templates would mix positions with different roles. The size of the reference set is **not stated** in the paper. |
| **Always log** | Reference distribution and how it was generated; whether the mean is per template / per position; **reference set size** (rule 4); metric; seed; model revision hash. |

## Why it exists

The obvious knockout — delete the node, i.e. set its output to zero — has a
flaw the paper states plainly: "0 is an arbitrary value, and subsequent nodes
might rely on the average activation value as an implicit bias term. Perhaps
because of this, we find zero ablation to lead to noisy results in practice"
[wang-2022 §2.1]. Mean ablation keeps the implicit bias and removes only the
per-input variation. The authors relate it to the bias-correction step of
Nanda & Lieberum's grokking analysis.

The page earns its place because D-006 commits E3 to running this alongside
zero and resample, and because the definition of a circuit Wang et al. use
(`C(x)` = the model with everything outside `C` knocked out) makes the
knockout method part of what "circuit" means; see [[circuit]].

## Intuition, then mechanism

**The analogy:** replacing a sensor's live reading with its long-run average.
Downstream systems calibrated to "a reading is usually about here" keep
working; only the information in *today's* reading is gone.

**Where it breaks.** "Long-run average over what?" is the whole method. Average
the sensor over days when the quantity of interest never changed and you have
removed nothing of interest. That is exactly the paper's reason for not
averaging over `p_IOI`: the fact that a name is duplicated is constant across
`p_IOI`, so the mean would carry it, and knocking out a Duplicate Token head
with that mean would leave the "duplicated" signal in place [wang-2022 §2.1].

**Mechanism** [wang-2022 §2.1]:

- The unit knocked out is a **(head, token position) pair** — a node in the
  computational graph — not a whole head at all positions.
- Reference distribution `p_ABC`: the `p_IOI` templates with the two names
  replaced by three unrelated random names A, B, C. Sentences keep their
  grammar and lose their single plausible indirect object.
- The mean is computed **across samples of the same template**, because the
  grammatical role at a given position differs between templates. All names,
  places and objects are single tokens "to ensure proper sequence alignment
  computation of the mean activations" [wang-2022 §App. E].
- "Mean-ablations remove the information that varies in the reference
  distribution (e.g. the value of the name outputted by a head) but will
  preserve constant information (e.g. the fact that a head is outputting a
  name)" [wang-2022 §2.1].

**One-line checkpoint:** the reference set defines the question; the mean
removes what varies over it and keeps what does not.

## Precisely

For a circuit `C` in the model's computational graph `M`, the paper defines
`C(x)` as the logits of `M` on `x` with every node in `M \ C` mean-ablated on
`p_ABC`, and `F(C) = E_{X ~ p_IOI}[ f(C(X); X) ]` with `f` the IO−S logit
difference [wang-2022 §2.1, §4]. Every faithfulness, completeness and
minimality number on [[circuit-validation-criteria]] is an `F` computed this
way.

Numbers from the paper that are mean-ablation results:

| Quantity | Value | Where |
|---|---|---|
| `F(M)`, clean model, over 100,000 samples | 3.56 | §2, §4 |
| `F(C)`, the 26-head circuit | `|F(M) − F(C)|` = 0.46, so `F(C)` ≈ 3.10 (derived) | §4 |
| Drop after knocking out the three Name Movers | ≈ 5% | §3.4, App. F |
| Largest greedy incompleteness score | 3.09 | §4.1 |
| MLP0 knocked out | sign of logit difference reverses | App. J |
| All MLPs except MLP0 knocked out | −1.1 | App. J |

The reference-set size behind the means is not given anywhere in Wang et
al.'s text. *Added 2026-09-19:* Miller et al., reproducing the setup,
state it as "around seven examples per template" [miller-2024 §4] — a
second-hand figure, recorded as such. Miller et al.'s own means are over
100 ABC prompts, and they find the IOI faithfulness score "monotonically
increases with the size of the ABC dataset" [miller-2024 §4.1, Fig. 4]. No
mechanism is proposed in the paper.

## What it licenses

Under rule 1: "under mean ablation on `p_ABC` (template-matched, per
position; reference size N), knocking out {nodes} changes mean logit
difference on `p_IOI` by {amount}." A necessity claim about the
distribution-varying part of what those nodes carry.

Two things the paper shows it does *not* license:

- **Faithfulness is not completeness.** The circuit reaches 87% of `F(M)`
  under this knockout, and a greedy search still finds subsets whose removal
  separates circuit and model by 87% of the baseline. See
  [[circuit-validation-criteria]].
- **A single-node number is not a stable property of the node.** The Backup
  Name Movers have the smallest minimality scores in the circuit — down to
  about 1% of `F(M)`, computed against `K` = the other name-moving heads —
  and carry the task after the Name Movers are removed [wang-2022 §4.2, App.
  F, App. K].

## Where it's contested

- **Zero ablation is dismissed in one sentence, without a comparison.** "Noisy
  in practice" is the entire evidence [wang-2022 §2.1]. D-006 treats the two
  as asking different questions; this paper treats one as a worse version of
  the other. Miller et al. side with D-006: mean and zero define different
  tasks — "given the context of outputting a name" versus including "the
  mechanism that decides it needs to output a name" [miller-2024 §6].
- **The reference set size is unstated in the source**, which is the exact
  omission rule 4 exists to prevent; Miller et al. put it at about seven
  per template and show the score moves with it. Any E2 reproduction has to
  choose one and say so.
- **Mean versus resample disagree, and neither is the refined one.** On
  IOI, resample gives systematically lower faithfulness at the node level;
  on Sports Players a mean-ablated model sits at chance while a
  resample-ablated one sits at 0% because the corrupt prompt carries a
  competing answer [miller-2024 §4.1, App. D.2]. See [[resample-ablation]].
- **Per-position ablation is not whole-head ablation.** E3's design (every
  head, one at a time, on a battery) ablates heads at every position. A
  faithfulness number computed that way is not comparable to Wang et al.'s.
  Proposed as O-013.

## What this project does with it

- **E1 harness:** the mean is computed on a *named reference distribution*
  with a *logged size*, per template and per position where the battery item
  has templates. The harness should make "which reference?" a required
  argument, not a default.
- **E2:** reproducing `F(C)` = 87% requires `p_ABC`, template-matched means
  and (head, position) nodes. Any deviation goes in the tolerance statement.
- **E3:** D-006's mean map is this method with the battery's own corruption
  set as reference. The choice of reference per battery item is a documented
  corruption-scheme decision (O-003).

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 2 · 2.1 · 3.4 · 4 · 4.1 · 4.2 · App. E · App. F · App. J ·
  App. K.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 3.1.3 · 4 · 4.1 (Fig. 4) · 6 · App. D.2.

## Open questions

- What reference-set size stabilises a template-matched mean on GPT-2 small?
  Measure at E1; rule 4 needs a number to log.
- Does mean-ablating a whole head at all positions on `p_ABC` reproduce the
  per-position result, and if not, by how much? (O-013.)
