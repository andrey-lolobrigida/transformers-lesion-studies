---
title: Causal tracing
type: method
status: drafted
sources: [meng-2022, miller-2024]
first-needed: E1
updated: 2026-09-20
---

# Causal tracing

*Drafted from a skim of Meng et al. (ROME), Section 2 and Appendix B. This
is the worked example of [[activation-patching]] in the **restore**
direction that the wiki was missing, and the reference setup for the
factual-recall battery item. Everything here is GPT-2 XL unless marked.*

## In one sentence

Corrupt the input so the model loses a fact, then put **one clean internal
state back at a time** and measure how much of the correct answer's
probability returns — a (token × layer) map of which states are enough to
recover the fact.

## Claim-licence block

| | |
|---|---|
| **Answers** | **Sufficiency**, given the corruption: "with the subject obfuscated, is restoring *this* state at *this* token enough to bring the correct object back?" This is Miller et al.'s "restore clean · circuit" cell [miller-2024 Table 3] with the circuit being a single state. |
| **Does NOT answer** | Necessity. A state that restores the fact when patched in is not thereby shown to be required on the clean run — nothing here ablates on a clean input. It also does not answer "where is the fact *stored*": that is a claim about weights, which the paper tests separately by editing (§3), and which the trace only motivates. |
| **Confounds** | The corruption rule is the experiment (see below): noise too small gives no total effect to mediate; noise of a different shape gives smaller effects. Single-vector restoration is nearly uninformative for MLP and attention *modules* — the paper restores windows of ten layers, so the "layer" on those maps is a window centre [meng-2022 App. B.2]. The effect is measured on the paper's own selection of facts the model already knows. |
| **Always log** | Corruption rule (which tokens; noise distribution; scale as a multiple of the embedding std; number of noise samples per prompt); restoration unit (single state vs window, and window width); which component family (hidden state, MLP output, attention output); the known-facts filter and how many prompts survived it; metric (probability of the correct object, or this project's logit difference — say which); model and layer numbering convention; seed; model revision hash. |

## Why it exists

The question is "where does a large language model store its facts?"
[meng-2022 §1], and the tool is causal mediation analysis after Vig et al.:
treat the grid of hidden states as a causal graph and ask which
intermediate variables carry the effect of the input on the output
[meng-2022 §2.1]. The paper's contribution to *method* is the paired
intervention — corrupt, then restore — that gives each state an indirect
effect; its contribution to *findings* is the early site.

The page exists because the roadmap names factual recall as "the ROME-style
setup" and `docs/01-methods.md` describes activation patching in exactly
this direction, but no source on the wiki had performed it until now.

## Intuition, then mechanism

**The analogy:** a witness has been drugged and can no longer recall a name.
You restore their memory of one moment at a time and see which single
moment, given back, lets them produce the name. The moments that do are the
ones the recall ran through.

**Where it breaks.** Restoring one moment does not show it was *needed* on
the sober day — other routes may have carried the same fact, and you only
learn what suffices under this particular drug. Change the drug (the
corruption rule) and the decisive moments can move. And "restoring a
moment" here is restoring a vector that everything downstream re-reads, so
what you measure includes every downstream readjustment.

**Mechanism** [meng-2022 §2.1, App. B.1]. Three runs on a prompt $p$
describing subject $s$ and relation $r$, whose correct completion is the
object $o$:

1. **Clean run.** Run $p$; cache every hidden state $h_i^{(l)}$ (token $i$,
   layer $l$), plus each layer's MLP output $m_i^{(l)}$ and attention output
   $a_i^{(l)}$.
2. **Corrupted run.** Immediately after embedding, add Gaussian noise
   $\epsilon \sim \mathcal{N}(0, \nu)$ to the embeddings of every token in the subject, with $\nu$
   set to **three times** the empirical standard deviation of token
   embeddings over a body of text. Run forward. Repeat with ten different
   noise samples per prompt. On the 1000 known facts this drops the mean
   $P[o]$ from 27.0% to 8.47% [meng-2022 App. B.1].
3. **Corrupted-with-restoration run.** Same noisy input, but at one chosen
   $(\text{token } i,\ \text{layer } l)$ hook the state to its clean value and let the rest
   of the forward pass proceed untouched.

The effects, with $P[o]$, $P_*[o]$, $P_{*,\,\text{clean}\ h}[o]$ the correct-object
probabilities under the three runs:

- **Total effect** $\mathrm{TE} = P[o] - P_*[o]$: what the corruption costs.
- **Indirect effect** of state $h_i^{(l)}$: $\mathrm{IE} = P_{*,\,\text{clean}\ h_i^{(l)}}[o] - P_*[o]$,
  the recovery from restoring that one state while the subject stays
  corrupted.
- **ATE, AIE**: the same, averaged over the prompt sample.

Footnote 3: the *direct* effect — the part of the corruption's effect that
"flows through other model components besides the chosen mediator" — was
computed and found "noisy and uninformative, in line with results by Vig et
al." [meng-2022 §2.1 fn. 3]. (This is not this project's "direct effect";
see "Where it's contested".)

**Restoring modules rather than states.** Restoring a *single* MLP output
$m_i^{(l)}$ or attention output $a_i^{(l)}$ "had generally negligible effects,
suggesting the decisive information is accumulated across layers". So for
the MLP and attention maps the paper restores a **run of ten consecutive
layers** centred on $l$, clipped at the edges, and plots the result at $l$
[meng-2022 App. B.2]. The hidden-state map (Fig. 1e/2a) is single-vector;
the MLP and attention maps (Fig. 1f–g/2b–c) are windows.

**One-line checkpoint:** three runs, one restored state, one probability
difference; the map is where the difference is large.

## Precisely

**What was found on GPT-2 XL**, 1000 facts, all figures in $P[o]$ and layer
indices from 0 [meng-2022 §2.2, App. B.1–B.2]:

| Quantity | Value |
|---|---|
| ATE | 18.6 percentage points |
| Peak single-state AIE, last subject token | 8.7 pp at layer 15 |
| Restoring the best single state at the last subject token, per prompt | raises $P[o]$ to 19.5% on average (27.0% clean, 8.47% corrupted) |
| Same, bucketed by layer, peak | 15.0% at layer 15 |
| MLP-window AIE peak, last subject token | 6.6 pp; window centred at layer 17 restores to 15.0% |
| Attention-window AIE at last subject token | 1.6 pp |
| Attention-window peak, last token of the prompt | centred at layer 32, restores to 16.5% |

Two sites: an **early site** — mid-layer MLP windows at the *last token of
the subject* — and a **late site** — late-layer attention at the *last
token of the prompt* [meng-2022 §2.2, Fig. 2]. The late site "is
unsurprising"; the early site is the paper's new finding.

**The path-specific test** [meng-2022 §2.2, Fig. 3]. To ask whether the
early-site hidden states matter *because of* the MLPs above them, the
authors sever the MLP modules at the subject token: freeze every later
MLP at that token in its corrupted-run value, so restoring a hidden state
below can no longer change what those MLPs output. With MLPs severed, low
layers "lose their causal effect"; high-layer states' effects "depend
little on the MLP activity". Severing attention instead shows no such
transition. This is a *freezing* intervention in the O-011 sense — a path
restriction layered on a restore-direction patch — and it is the closest
thing in the paper to a necessity claim about MLPs, though still on the
corrupted input.

**Corruption-rule robustness** [meng-2022 App. B.4]:

- Also corrupting the token *after* the subject: "substantially the same",
  effects somewhat reduced, early site still at the last subject token
  (Figs. 12, 15).
- Noise much smaller than $3\sigma$: ATE "become[s] very small" and the
  indirect effects are hard to discern. **Noise has to be big enough to
  make a total effect.**
- Uniform noise, or Gaussian with the embeddings' empirical mean and
  covariance: traces still work, effects smaller (Fig. 13).
- Integrated gradients "does not yield the same insights" (Fig. 16) —
  stated, not examined here.

**Across models** [meng-2022 App. B.3]: GPT-2 Medium, GPT-2 Large, GPT-J,
GPT-NeoX all show an early site of MLP effects at the last subject token,
"although the layers where effects peak are different from one model to
another". Larger models show negative effects at pre-subject tokens, and
attention effects appear earlier in the stack in the Eleuther models.
GPT-2 small is not traced.

**The loop closed from the other side** [meng-2022 §3.4, App. I]: ROME
edits at every (layer, token) work best at the last subject token in the
middle layers, with generalisation peaking at layer 18, "the middle layers
of the early site"; editing late-layer attention (AttnEdit at layer 33)
regurgitates the target on the original prompt but does not generalise to
paraphrases. This is a weight-editing result and is what licenses the
paper's storage claim; the trace alone does not.

## What it licenses

- "Under causal tracing on {model} with {corruption rule}, restoring
  {state | window of k layers of component family} at {token} raises the
  correct-object probability from {corrupted} to {restored}, out of
  {clean}." **Sufficiency of that state, given that corruption.**
- The severed-MLP comparison licenses "the effect of restoring low-layer
  hidden states at the subject token runs through the later MLPs at that
  token" — a path claim, on the corrupted input.
- It does **not** license "facts are stored in the MLPs". The paper makes
  that claim with §3, by editing the weights and checking generalisation
  and specificity. Written as a tracing result alone, it would be a
  sufficiency-to-storage leap. Epistemic rule 2.

## Where it's contested

- **"Direct effect" collides with this project's term.** ROME's direct
  effect (fn. 3) is Pearl's: the corruption's effect that bypasses the
  mediator. This project's direct effect (O-011 resolution;
  [[path-patching]]) is a component's own contribution to the logits with
  every other path frozen. ROME's finding that its direct effect was
  "noisy and uninformative" says nothing about ours. Do not cite fn. 3 as
  evidence either way about E3's direct-effect maps.
- **The window is doing work.** A per-layer MLP map built from single-layer
  restorations would look nearly blank; the early site appears only when
  ten layers are restored together. Miller et al. classify ROME's
  granularity as "layers" [miller-2024 Table 2]; more precisely it is
  *single hidden states* for one map and *ten-layer windows of one module
  family* for the other two. Any E3 per-layer MLP row is the single-layer
  version and should expect the blank.
- **Miller et al.'s "Gaussian noise (ROME)" as an ablation value**
  [miller-2024 §3.1.3] and ROME's own description differ in emphasis: in
  ROME the noise is the *input corruption* on the embeddings, and the
  intervention on the mediator is *resample-clean*. In six-tuple terms the
  experiment is (states or layer-windows · node · restore clean · specific
  token · circuit = one state) with noise as the corrupt distribution. Both
  readings are consistent; the distinction matters when E1 records what a
  corruption scheme removes and inserts (O-003 resolution).
- **The last subject token is not always the site** [meng-2022 App. B.4,
  Fig. 11]: "Windows Media Player" triggers the lookup at "Windows";
  "Madame de Montesson" at "Madame"; some low-confidence traces have no
  decisive subject token. The averaged map hides this.
- **Nothing here is on GPT-2 small, and nothing is a logit difference.**
  Both translations are the project's.

## What this project does with it

- **E1 factual-recall battery item** (roadmap E1; O-009). The reference
  setup is: prompts from a fact set, filtered to those the clean model
  answers (ROME's rule: greedy generation names $o$ before any other
  capitalised word, text before $o$ becomes the prompt) [meng-2022
  App. B.1]; corruption = Gaussian noise on subject-token embeddings at
  $3\sigma$, ten samples; metric translated to logit difference per rule 5,
  with the $P[o]$ version kept alongside for comparability. The filter
  count is a battery artifact field.
- **O-007 (MLPs first-class).** Third datapoint, after Wang and Miller:
  causal tracing's headline is an MLP result, at the level of ten-layer
  windows. A harness that hooks only heads cannot run the factual-recall
  item's own reference experiment.
- **E2 verification direction.** The wiki now has one sourced example per
  direction: Wang et al. (ablate clean, necessity) on
  [[activation-patching]], and this page (restore clean, sufficiency).
  The E2 results doc names which one it ran.
- **O-003.** ROME's App. B.4 is a small worked instance of sweeping the
  corruption scheme: the site survives an extended corruption and a
  changed noise shape, and vanishes when the noise is too small to cost
  anything.

## Sources

- [meng-2022] Meng, Bau, Andonian & Belinkov, "Locating and Editing
  Factual Associations in GPT", arXiv 2202.05262v5. Sections cited: 1 ·
  2.1 (fn. 3) · 2.2 (Figs. 2, 3) · 2.3 · 3.4 · App. B.1 · B.2 · B.3 ·
  B.4 (Figs. 11–13, 15, 16) · App. I.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1. Sections
  cited: 3.1.3 · Table 2 · Table 3.

## Open questions

- Does GPT-2 small show an early site at all, and at what window width?
  Measured at E1, not guessed (O-009).
- What does the trace look like in logit difference rather than $P[o]$?
  The battery README records the answer next to the $P[o]$ version.
- Is a ten-layer window meaningful in a 12-layer model, or does E1 need a
  narrower one? The paper gives no rule for choosing the width.
