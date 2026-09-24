# 02 — Roadmap

Two tracks. **R phases are reading only — no code, no environment setup, no
"quick experiments."** E phases are experimental. Some R phases gate specific E
phases; those gates are marked and are not negotiable, because the whole point
of a reproduction-first project is not making claims you have to retract.

Each phase has an exit criterion. A phase is done when the criterion is met and
the tag is cut, not when it feels done.

**Minimum shippable project:** R0, R1, E0–E4. That is a complete, honest piece
of work.

---

## Reading track

### R0 — Orientation
*No code. Estimated 1–2 weeks of evening reading.*

**Goal:** hold the mental model before touching anything. Specifically: what a
circuit is, how to reason about an attention head in terms of QK and OV, and
what an induction head does.

**Read:** Olah et al. "Zoom In" · Elhage et al. "A Mathematical Framework for
Transformer Circuits" (QK/OV sections at minimum) · Olsson et al. "In-context
Learning and Induction Heads".

**Exit criterion:** a note in `notes/` explaining, in your own words and
without looking: what a circuit is, what the QK and OV circuits of a head do,
what an induction head computes, and why it might relate to in-context
learning. If any of those can't be written cold, R0 isn't finished.

---

### R1 — Methods and epistemics
*No code. Gates E1 onward. Estimated 1–2 weeks.*
**Closed 2026-09-20, tag `v-R1`** (D-010 closure in `docs/04-decisions.md`).

**Goal:** know what each measurement licenses before generating any numbers.

**Read:** Wang et al. IOI paper (the canonical ablation + patching case study,
and the source of the backup-head phenomenon) · Miller, Chughtai & Saunders
"Transformer Circuit Faithfulness Metrics are not Robust" · Meng et al. ROME
(skim, for causal tracing) · Chan et al. causal scrubbing (skim, for the shape
of the rigour endgame).

**Exit criterion** *(revised 2026-09-19, D-010)*: Wang et al. and Miller et
al. are extracted into the wiki; `docs/01-methods.md` has been reviewed against
those pages and edited by the author wherever it is wrong or missing — it
states, for this project specifically, what claim each ablation type licenses
and what the default metrics are, and it is the thing that prevents sloppy
claims in E3 and E4; and every item pinned to R1 in `docs/04-decisions.md`
(O-003, O-007, O-011's trigger, the circuit-definition reconciliation, the
Miller-vs-pattern-preserving-ablation check) is resolved or explicitly
deferred. The other listed papers are skims and do not gate.

---

### R2 — Self-repair
*No code. Gates E4. Estimated 1 week.*

**Goal:** understand the phenomenon the project's spine attacks, including the
parts of it that are mundane.

**Read:** Rushing & Nanda "Explorations of Self-Repair in Language Models"
(arXiv 2402.15390) · McGrath et al. "The Hydra Effect" (arXiv 2307.15771) ·
"Conditional Co-Ablation" (arXiv 2607.01940) — recent, directly adjacent, read
before committing to E4.

**Key prior finding to internalise:** LayerNorm rescaling accounts for a
substantial share of apparent self-repair — reportedly up to around 30% of the
ablated direct effect — and it is entirely mechanical. Removing any additive
contribution from the residual stream reduces its norm, so LayerNorm divides by
a smaller factor and amplifies everything that remains, regardless of what the
removed component computed. Self-repair is also reported as imperfect and noisy
across prompts, sometimes overcorrecting. And a portion remains unexplained
after accounting for LayerNorm and known backup heads.

**Exit criterion:** a written statement of the specific open residual E4 will
attack, and an honest assessment of whether the recent adjacent work has
already closed it. If it has, E4 gets redesigned or replaced — that decision
goes in the log.

---

### R3 — Field map
*No code. Optional, do before any decision to aim at a venue.*

**Read:** "Open Problems in Mechanistic Interpretability" (arXiv 2501.16496) ·
Tigges, Hanna, Yu & Biderman, "LLM circuit analyses are consistent across
training and scale" (arXiv 2407.10827).

**Exit criterion:** a shortlist of gaps this project could plausibly touch,
with an honest note on which are already crowded.

---

## Experiment track

### E0 — Environment and smoke test
*Small. Half a day if nothing goes wrong, a weekend if the GPU fights back.*

Get TransformerLens running on the 5060, load GPT-2 small, run a forward pass,
hook an activation, and confirm one published number reproduces exactly (a
logit difference on a handful of IOI prompts is a good choice).

**Exit criterion:** one command in the repo reproduces one published number.
Environment gotchas recorded in `docs/06-environment.md`.
**Tag:** `v-E0`

---

### E1 — Task battery and harness
*Gated on R1. The phase most likely to be underestimated — budget real time.*
**Split 2026-09-20 into E1a (harness) and E1b (battery), run in that order
(D-012).** The description below is unchanged; the exit criteria and tags
are per sub-phase at the end.

This is not free infrastructure, it's the experimental design. Build, for each
capability, a dataset of clean/corrupted prompt pairs plus a metric:

- **Indirect object identification (IOI)** — has published numbers to check against
- **Subject–verb agreement** — grammatical, structurally simple. *Moved to a
  fallback 2026-09-23 (D-013): enters only if factual recall fails its
  clean-accuracy gate, and then as an explicitly unsourced item.*
- **Factual recall** — the ROME-style setup
- **Induction / in-context copying** — synthetic, easy to generate cleanly

**Deliberately excluded: arithmetic.** GPT-2 small does not do it well enough
for lesion results to be anything but noise. If arithmetic is wanted later, it
needs a model that can actually do it.

The harness should support zero, mean, and resample ablation over any
component — **attention heads and MLP layers both, as first-class hook
families** (O-007, resolved 2026-09-20; neurons stay out per D-003) — with
the mean-ablation dataset size logged automatically, and should emit a
per-run artifact with seed and model revision.

It also carries, per Miller et al.'s six-tuple, a **component type**
setting — *node* ablation (the change propagates everywhere downstream) or
*edge* ablation (only a named destination receives it; edge-to-logits is
Wang et al.'s path patching and is this project's *direct effect*, with the
MLP convention recorded as a flag) — and a **position mask** per ablation,
"all positions" being one value of it (O-013). Separately, the harness
implements **pattern freezing** (all attention patterns pinned to their
clean-run values, per Olsson et al.), which E2's induction reproduction
requires and which is this project's own axis, not a literature-standard
one. Direct effect is recorded per head alongside the node-level total effect
in the same run; the gap between them is the self-repair number E4 starts
from. Decided in the O-011 resolutions (2026-09-08 and 2026-09-19); the
reasoning is there.

**E1a — harness. Exit criterion:** the harness ablates an arbitrary head
or MLP layer under all three substitution methods from one CLI call, at node
or edge level, with any position mask, with or without pattern freezing,
recording every one of those settings in the artifact — a default that goes
unstated becomes a permanent choice nobody made. Validated on IOI, the one
item that already exists: an identity intervention reproduces the E0 clean
baseline bitwise, and mean-ablating MLP0 on `p_ABC` reverses the sign of the
mean logit difference [wang-2022 App. J] — a bracket, not a match (D-011).
**Tag:** `v-E1a`

**E1b — battery. Exit criterion:** every battery item has a clean/corrupted
generator, a metric with its expected direction under damage, and a
documented corruption scheme stating what it removes and what it inserts.
O-009 (factual-recall filter, per-item clean-accuracy gate, control item)
resolves here.
**Tag:** `v-E1b` — this is what E2 is gated on.
*Built 2026-09-23 on `phase-E1b-battery`; see `results/E1b/README.md`.
Gate: IOI pass, induction pass, factual recall fail (64 admitted survivors
against 300), so D-013's fallback is triggered. Subject–verb agreement (ours,
unsourced) was built 2026-09-24 under the D-013 addendum and passes its gate
(`number_flip`, n = 2,000, seed 0, BOS: pairwise accuracy 0.983, gap
+5.169 ± 0.041). Awaiting the author's review and `v-E1b`.*

---

### E2 — Reproduction
*The trust-building phase. Nothing after this is worth doing if this fails.*

Reproduce the induction head end to end: find it by ablation *and* verify it by
activation patching. Same for the core of the IOI circuit. Numbers should match
the literature within a stated tolerance.

**Exit criterion:** a results doc stating, per reproduced result, the published
number, our number, the tolerance, and whether it matched. **A failure to
reproduce is a valid and interesting exit** — it goes in the log at full
strength and probably changes the roadmap.
**Tag:** `v-E2`

---

### E3 — Functional map
*The first original output.*

Zero-, mean-, and resample-ablate every head in GPT-2 small, one at a time,
scored on the full E1 battery. Produce the heatmaps — one per ablation method,
shown together, never one alone.

*Four maps, not three, per the O-011 resolution:* the three above at total
effect, plus the pattern-preserving variant of whichever substitution method R1
settles as the in-distribution default, with the delta against its unfrozen twin
reported. A large delta escalates to the full cross; a small one is a logged
negative result. Detail lives in the decision log, not here.

The comparison across ablation methods is the actual content here. If the three
maps agree, that's a finding about robustness. If they disagree, the pattern of
disagreement is more interesting than either map.

**Exit criterion:** three heatmaps plus a written interpretation that states,
for every claim, which ablation method supports it and whether it is a
necessity or sufficiency claim. Any head singled out as important gets verified
with activation patching before it is named.
**Tag:** `v-E3`

**Decision point:** after E3, confirm or replace the E4 spine based on what the
maps actually showed.

---

### E4 — Self-repair, with the mechanical component controlled for
*Gated on R2. The intended spine.*

**The question:** how much self-repair survives once LayerNorm rescaling is
accounted for, and which components are performing compensatory computation as
opposed to being passively amplified by the normalizer?

Sub-questions, in rough order:

1. Measure self-repair per ablated head; decompose into the LayerNorm-rescaling
   share and the residual.
2. Does the split differ between zero, mean, and resample ablation? (Prior work
   suggests it does; confirming and characterising this is useful in itself.)
3. In the residual — the part that is not mechanical — which components step
   up, and is the pattern predictable from anything measurable in advance?
4. Do compensating components themselves have compensators, once the mechanical
   share is removed from both measurements?

**Exit criterion:** a results doc that reports the mechanical/residual split
per head under each ablation method, with the necessity/sufficiency status of
each claim stated. Honest failure mode to watch for: the residual may be small
and noisy, in which case that is the finding.
**Tag:** `v-E4`

**This is the point at which the minimum shippable project is complete.**
Writeup happens here regardless of whether E5/E6 follow.

---

### E5 — Cross-task circuit overlap *(sketch only — plan when reached)*

Do the components implicated in grammar overlap with those implicated in
factual recall? Shared substrate or clean localisation? Falls out of E3's data
almost for free, which is why it's cheap to attempt and easy to over-read.

### E6 — Circuit formation over training *(sketch only — plan when reached)*

Use Pythia's per-step checkpoints to ask when a circuit first appears. Open
questions to resolve before planning: do Pythia 70M/160M form clean induction
heads at all, and are the early checkpoints dense enough in the window where
formation happens? Decide deduped vs non-deduped once and never mix.

Prior work (Tigges et al. 2024) reports circuit structure is fairly consistent
across training and scale — so there is something to build on and to stress-test.

---

## Phase dependency summary

```
R0 ──> R1 ──┬──> E1a ──> E1b ──> E2 ──> E3 ──> E4 ──> [ship]
            │                             │      ↑
      E0 ───┘                             │   R2 ┘
                                          └──> E5, E6 (optional)
```
