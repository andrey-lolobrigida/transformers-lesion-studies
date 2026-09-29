---
key: meng-2022
title: Locating and Editing Factual Associations in GPT
authors: Meng, Bau, Andonian, Belinkov
year: 2022
venue: arXiv preprint (v5, 13 January 2023); MIT CSAIL / Northeastern / Technion. NeurIPS 2022 [unverified from this copy — the v5 text names no venue]
arxiv: 2202.05262   # verified: printed on the arXiv HTML page header, "arXiv:2202.05262v5 [cs.CL] 13 Jan 2023"
url: https://arxiv.org/abs/2202.05262
local: papers/meng-2022-rome/2202.05262.html
phase: R1
extraction: partial      # skim, by design: causal tracing only (D-010 item 1 — ROME does not gate)
feeds:
  - causal-tracing
  - activation-patching
  - ablation-methodology
---

# Source card — Meng, Bau, Andonian & Belinkov 2022 (ROME)

Read from the arXiv v5 HTML rendering (local copy). Four authors; Meng and
Bau equal contribution. Code, CounterFact dataset and an interactive demo at
`https://rome.baulab.info/`.

**Two halves.** Section 2 is *Causal Tracing*: activation patching in the
restore direction, over a (token × layer) grid of hidden states, MLP outputs
and attention outputs, on GPT-2 XL (48 layers, 1.5B parameters). Section 3
is *ROME*: a rank-one weight edit to one mid-layer MLP, evaluated as a
model-editing method on zsRE and on the authors' CounterFact dataset against
fine-tuning and two hypernetwork editors. The skim reads Section 2 as the
source for E1's factual-recall battery and for O-007; Section 3 is read only
where it feeds back into the tracing claim (§3.4, App. I).

**Evidence base for the tracing half:** 1000 factual prompts that GPT-2 XL
already answers correctly, selected from CounterFact by greedy generation;
corrupted by Gaussian noise on the subject-token embeddings; effect
measured as the probability of the correct object token. Also traced:
GPT-2 Medium and Large, GPT-J (6B), GPT-NeoX (20B). **Not GPT-2 small.**

## Structure

| Section | What it holds |
|---|---|
| 1 Introduction | "Where does a large language model store its facts?" |
| 2 | The (token × layer) grid; eq. 1 (the residual with attention after MLP) |
| 2.1 | Causal tracing: clean / corrupted / corrupted-with-restoration runs; TE, IE, ATE, AIE; footnote 3 on the direct effect |
| 2.2 | Results on GPT-2 XL: early site (mid-layer MLP, last subject token) and late site (late attention, last token); the severed-MLP path-specific test (Fig. 3) |
| 2.3 | The localized factual association hypothesis: MLP · middle layers · last subject token |
| 3.1 | ROME: the MLP as a linear associative memory; rank-one update (eq. 2) — *not extracted* |
| 3.2–3.3 | zsRE; CounterFact and its metrics (efficacy, generalization, specificity, fluency, consistency) — *not extracted* |
| 3.4 | Editing at each (layer, token) confirms the tracing site; generalization peaks at layer 18 |
| 4 | Related work: Vig et al. causal mediation; Geva et al. MLPs as key–value memories |
| App. B.1 | Experimental settings: prompt selection, noise scale, ten noise samples, single-vector restoration |
| App. B.2 | MLP and attention effects need *runs* of ten layers to show; single vectors "generally negligible" |
| App. B.3 | Traces on GPT-J, GPT-NeoX, GPT-2 Medium and Large |
| App. B.4 | Corruption-rule variants; noise must be large enough; integrated gradients comparison |
| App. I | AttnEdit: editing late-layer attention regurgitates but does not generalise |

## Extraction log

**2026-09-20 — partial (skim, causal tracing only).**

Read §1, §2 in full, §3 opening and §3.4, §4, §5, App. B and App. I from
the local HTML copy. Opened [[causal-tracing]] (the restore-direction
worked example that [[activation-patching]] had a slot for; the
factual-recall battery's reference setup). Edited [[activation-patching]]
(open question resolved; footnote 3 on the direct effect recorded under
"contested") and [[ablation-methodology]] (Table 2's ROME row annotated:
the noise is the input corruption, the ablation value is resample-clean;
the granularity note that ROME's MLP effects appear only in windows of
layers). Terms proposed for `docs/05-glossary.md`. Addenda proposed to
O-007 (the third datapoint the final call was waiting on), O-009 (ROME's
known-facts filter is the mechanism O-009 proposes) and O-011 (a
terminology collision on "direct effect").

**Deliberately left:**

- **ROME itself** (§3.1, App. A, App. E): the associative-memory derivation
  and the rank-one update. A weight intervention, not an activation one;
  nothing in E1–E4 edits weights.
- **The editing evaluation** (§3.2–3.4 metrics, Table 4, App. C, D, F, G,
  H, J): zsRE, CounterFact's construction, baselines, human evaluation.
  Only the one sentence of §3.4 that closes the loop on tracing (edits
  work best where tracing peaks) is used.
- **App. B.3's larger-model traces** beyond the one point that the site
  pattern recurs across sizes with the peak layer moving.
- **The integrated-gradients comparison** (Fig. 16): recorded as a claim,
  not examined.

**Recorded source gaps** (flagged on the pages):

1. **No GPT-2 small trace.** The smallest model traced is GPT-2 Medium
   (App. B.3, Fig. 9). Every number on [[causal-tracing]] is GPT-2 XL
   unless marked. O-009's worry stands unmeasured.
2. **Most results are heatmaps.** The text gives ATE 18.6%, the peak
   single-state AIE 8.7% (layer 15), the MLP-run peak 6.6% and the
   attention peak 1.6% at the last subject token (§2.2), plus the App. B
   restoration averages. Confidence intervals are in Fig. 7 only.
3. **The metric is a probability, not a logit difference.** All effects
   are differences of $P[o]$, the correct object's probability. Nothing in
   the paper reports a logit-difference version; epistemic rule 5 makes
   that this project's default, so E1's factual-recall metric is a
   *translation*, not a reproduction, and the battery README must say so.
4. **Footnote 3's "direct effect"** is Pearl's mediation-analysis direct
   effect (the corruption's effect that bypasses the chosen mediator),
   not this project's "a head's own contribution to the logits". Same
   words, different quantity — see the O-011 addendum.
5. **v5, not v1.** The card's key follows the arXiv v1 year (2022) as for
   `wang-2022`; the text read is v5 (January 2023).

**Not resolvable from this source, carried on the pages:** whether GPT-2
small shows an early site at all, and at which layer; what the
logit-difference version of the trace looks like; whether the
window-of-ten-layers finding (App. B.2) holds at 12 layers.

## Note on citing

Numbered sections and lettered appendices, with sub-numbered appendix
sections. Wiki citations: `[meng-2022 §2.1]`, `[meng-2022 App. B.2]`,
`[meng-2022 §2.1 fn. 3]`, figures by number. Layers are numbered from 0 in
the by-layer results [meng-2022 App. B.1]. The arXiv ID is verified from
the page header; the venue is not stated in the v5 text.
