# 07 — Alignment extension (parked)

**Status: parked. Not planned, not scheduled, not committed to.**

This document exists so a possibility isn't lost, not because it's on the
roadmap. Per the project's just-in-time principle, nothing here gets planned in
detail until E4 has shipped and there's a reason to plan it. Treat it as a
parking lot with reasoning attached.

**Do not start any of this before the minimum shippable project (R0–R1,
E0–E4) is complete.** The value of the extension depends on having a validated
harness and calibrated epistemic habits; starting here first gets you fuzzy
results from unvalidated tooling, which is the worst combination available.

---

## The structural obstacle, stated first

Interpretability scales down gracefully. Circuits exist in GPT-2 small, so they
can be studied on a desktop. **Most alignment questions do not scale down.** A
124M model cannot scheme, cannot sandbag, cannot strategically deceive — the
behaviours of concern are frequently the ones that emerge above the size that
fits on this hardware.

This is the real constraint on hobbyist alignment work, and it is not a compute
problem that a bigger card solves. It means the only tractable direction is:
**pick an alignment-relevant behaviour that small models actually exhibit, and
apply the same methods to it.** Everything below follows from that.

---

## Direction A — Refusal as a lesion target

The strongest candidate, because it is already a lesion study.

Arditi et al. (2024, NeurIPS) found that refusal in aligned models is mediated
largely by a single direction in the residual stream: erase that direction and
the model stops refusing; add it and it refuses harmless prompts. Same method
as this project, same epistemics, applied to a safety-relevant behaviour rather
than subject–verb agreement.

**Hardware fit:** small instruct models that actually refuse — Qwen 2.5 1.5B,
Llama 3.2 1B, Gemma 3 1B — run comfortably in 8 GB.

**Why it suits reproduction-first:** the single-direction claim has already
been complicated in useful ways. Follow-up work in early 2026 argues that
treating refusal as one-dimensional ignores the distributional structure of the
activations, and reports that intervening at only 1–2 layers around 40–60% of
network depth outperforms full-network intervention — implying refusal
mechanisms may be more localised than the original framing suggests. That is
precisely a "where does the published result stop holding" question, which is
this project's mode.

**Candidate questions**, in the register of E3/E4:

- Does the single-direction result hold under the ablation-method comparison
  this project already runs? Zero, mean, and resample ablation of the direction
  are three different interventions.
- Where in depth does refusal actually live, and is the localisation stable
  across model families?
- Does refusal exhibit self-repair the way ordinary circuits do? If safety
  behaviour has backup mechanisms, that's a substantively different picture
  from the single-direction story — and it's the direct transplant of E4.

**Dual-use note, to decide up front rather than at writeup time.** This
technique is the basis of "abliteration" — removing safety guardrails from
open-weight models — and there is productised tooling for it. The research is
legitimate and published; the tooling around it is not neutral. The workable
position is to release measurement and analysis, not an improved removal
method, and to not publish artifacts whose main use is stripping guardrails.
Decide this before starting, because it constrains what the experiments should
even be.

---

## Direction B — Knock-in instead of knockout

The complementary move, and the more conceptually interesting one.

This project is a **knockout study**: remove a function, observe the deficit.
Genetics has a matching tool — the **knock-in**, where a defect is deliberately
installed into a model organism, so the ground truth is known by construction.

The alignment version already exists under almost that name: *model organisms
of misalignment*, of which "Sleeper Agents" (Hubinger et al., 2024, arXiv
2401.05566) is the canonical case — deliberately train a backdoored model, then
test whether standard safety training removes the backdoor. It largely did not.

**Why this is attractive at this scale:** training a small backdoored model at
TinyStories or small-Pythia scale is feasible on this hardware, and it solves
the hardest problem in interpretability — that you never actually know what the
circuit is. When you planted the mechanism yourself, you have ground truth.

**The pairing that makes this more than a second project:**

> Use knock-in models as a calibration standard for the knockout methods.

Plant a known mechanism, then check whether the E1 harness recovers it. If the
ablation pipeline cannot find a circuit that was deliberately built and whose
location is known, that is a direct, quantitative statement about what the E3
heatmaps are worth. Every method in this project is currently trusted on the
strength of matching published numbers; this would let it be trusted on the
strength of a controlled test.

That calibration angle is arguably worth doing **even if the alignment
extension never happens**, which is the one part of this document that might
justify pulling forward. Flag it at the E4 retrospective.

---

## Direction C — Secondary candidates (thin sketches)

Listed for completeness. None investigated.

- **Sycophancy.** Measurable behaviourally, present in small models, has
  published characterisation (Sharma et al., 2023). Would slot into the E1
  battery as another task.
- **Chain-of-thought faithfulness.** Does stated reasoning match the causal
  reasoning? (Turpin et al., 2023.) Requires models capable of CoT, so pushes
  toward the top of what fits locally.
- **Steering vectors, mechanistically.** Contrastive activation addition
  (Rimsky et al., 2024) and the question of how steering interacts with
  specific components rather than whether it works. Recent work looks directly
  at this.

---

## What is harder here than in the core project

Two things, both worth taking seriously before activating any of this.

**Evaluation is fuzzier.** "The logit difference dropped by 0.3" is a fact.
"The model deceived" is a judgment. This project's epistemic rules were written
for the crisp case; soft metrics plus solo work plus no peer review is an ideal
environment for self-deception. Any alignment extension needs its measurement
rules rewritten before it needs its experiments designed.

**Less crisp prior work to reproduce.** Reproduction-first has less traction in
a younger and more contested literature. Refusal is a happy exception — a
specific, famous, checkable claim — which is part of why Direction A ranks
first.

---

## Deferred reading (do not start before E4 ships)

- Arditi et al., 2024 — "Refusal in Language Models Is Mediated by a Single
  Direction" (NeurIPS 2024). The anchor.
- Nanfack, Belilovsky & Dohmatob, 2026 — "Efficient Refusal Ablation in LLMs
  through Optimal Transport" (arXiv 2603.04355). The complication: refusal as
  distributional rather than one-dimensional, and the layer-depth localisation
  finding. `[verify venue before citing]`
- "What Drives Representation Steering? A Mechanistic Case Study on Steering
  Refusal" (arXiv 2604.08524). How steering vectors interact with components.
  `[verify authors before citing]`
- Hubinger et al., 2024 — "Sleeper Agents: Training Deceptive LLMs that Persist
  Through Safety Training" (arXiv 2401.05566). The knock-in anchor.
- Sharma et al., 2023 — "Towards Understanding Sycophancy in Language Models"
  (arXiv 2310.13548).
- Turpin et al., 2023 — "Language Models Don't Always Say What They Think"
  (arXiv 2305.04388).

---

## Activation criteria

This document stops being a parking lot when all of the following hold:

1. E4 has shipped, with a writeup.
2. There is a specific question here worth more than continuing the core
   project into E5/E6.
3. The measurement rules have been rewritten for soft-metric work, and the
   dual-use position has been decided in writing.

Until then, it stays parked, and the next session should not treat it as a plan.
