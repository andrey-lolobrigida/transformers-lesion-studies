# Wiki — the project's conceptual reference

This is where the reading phases deposit what they produce. It is organised by
**concept**, not by paper: reading a paper is an extraction pass whose output is
merged into concept pages. No paper has a page of its own.

Decision and reasoning: `D-009` in `docs/04-decisions.md`.

---

## What this is for, and what it is not

Two readers, one artifact.

- **For Andrey**, it is a place to consolidate and to check against. It is
  *not* the R-phase deliverable. Exit criteria are unchanged: R0's note in
  `notes/` is still written cold, in your own words, without opening these
  pages; R1 means reviewing `docs/01-methods.md` against the extracted pages
  and editing it yourself (D-010, not a cold rewrite). Read the wiki
  page *after* writing the note, and treat the difference between them as the
  actual result of the exercise.
- **For Claude**, it is the implementation reference at E1 and after. When the
  harness needs to know what resample ablation licenses, the answer is on
  `methods/resample-ablation.md`, already reconciled across sources.

`notes/` holds your thinking. `wiki/` holds the field's. Keeping them in
separate directories is what makes the comparison meaningful.

## Layout

```
wiki/
├── README.md      ← this file
├── concepts/      ← what a thing IS      (circuit, feature, induction head,
│                    self-repair, superposition)
├── methods/       ← what you DO to it    (zero/mean/resample ablation,
│                    activation patching, logit difference)
└── sources/       ← one thin card per paper
```

Phenomena — self-repair, the Hydra effect — file under `concepts/`.

The concept/method split is not cosmetic: the epistemic rules in `CLAUDE.md`
are almost entirely about methods, and E1's harness is built out of the method
pages. It is the cut that maps onto code.

## What earns a page

> **A concept earns a page when getting it wrong would change an experiment or
> a claim.**

*Logit difference* earns one — epistemic rule 5 makes it the default metric,
and confusing it with loss changes every number in E3. *Softmax* does not.
Anything that needs one line and no argument goes to `docs/05-glossary.md`.

Pages open **on first need, from a paper actually read**. Do not build a
taxonomy in advance. Stubs are fine and are marked `status: stub` — a stub
records that a concept exists and is not yet understood, which is information
worth having.

## Page anatomy

```yaml
---
title: Induction head
type: concept          # concept | method | phenomenon
status: stub           # stub | drafted | settled
sources: [olsson-2022, elhage-2021]
first-needed: E2       # the phase that will need this
updated: 2026-08-30
---
```

Sections, in order. Omit any that is genuinely empty except **1**, **5**, and
**8**:

1. **In one sentence.** The compressed version. If this cannot be written, the
   page is not ready.
2. **Why it exists.** The problem it solves, before the solution.
3. **Intuition, then mechanism.** The analogy first, the rigour immediately
   after, and an explicit note on where the analogy breaks. An analogy left
   alone leaves the reader confidently wrong.
4. **Precisely.** Notation and definition. This is the section read at
   implementation time.
5. **What it licenses.** For a concept: what observation would demonstrate it.
   For a method: what claim it supports, in the necessity/sufficiency
   vocabulary of epistemic rules 1–2. Mandatory.
6. **Where it's contested.** Disagreements between sources, robustness caveats,
   known failure modes. Never deleted — an empty one means "no contest found in
   sources read so far", which is a claim with a date attached.
7. **What this project does with it.** Links to phases, battery items, decision
   IDs. This is what makes the page an implementation reference rather than a
   textbook chapter.
8. **Sources**, per claim: `[olsson-2022 §3]`. Not a bibliography at the
   bottom.
9. **Open questions.** If one turns out to be project-level, it graduates to an
   `O-00N` in `docs/04-decisions.md`.

### Method pages: the claim-licence block

Mandatory, immediately after section 1. This is where the epistemic rules stop
being aspirational:

| | |
|---|---|
| **Answers** | Necessity — "does behaviour break without this component?" |
| **Does NOT answer** | Sufficiency. A necessity result is never written in restore-language. |
| **Confounds** | What makes the number lie, and in which direction |
| **Always log** | mean-ablation dataset size (rule 4), seed, model revision hash |

## Source cards

`wiki/sources/<first-author>-<year>-<slug>.md`:

```yaml
---
key: olsson-2022
title: In-context Learning and Induction Heads
year: 2022
venue: Anthropic / Transformer Circuits Thread
arxiv: <not yet verified>
url: https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/
local: —                     # path under papers/ if a copy was saved
phase: R0
extraction: not-started      # not-started | partial | complete
feeds: [induction-head, attention-head]
---
```

Followed by a dated **extraction log**: what pass was done, what was
deliberately left. **No summary prose** — a card must never be readable as a
substitute for the paper.

arXiv IDs stay `<not yet verified>` until checked against the paper itself.
`CLAUDE.md` forbids invented citations, and an ID that looks plausible is
exactly how that rule gets broken.

## Sourcing

Pages are written from the actual text — the URL in the source card, or a local
copy under `papers/` (gitignored) — never from recall. Every substantive claim
carries a section pointer.

This matters more than it might seem. Claude's training data ends around May
2026, so `arXiv 2607.01940` (Conditional Co-Ablation, ~July 2026) is entirely
outside it — and that is the paper that resolves `O-001` and decides whether
the E4 spine survives.

## Voice

`curious-student` register (`~/.claude/output-styles/curious-student.md`):
jargon introduced rather than assumed, analogy first and rigour immediately
after, the why before the how, a one-line checkpoint closing a substantial
explanation.

Two overrides:

- **Sober register wins.** `CLAUDE.md` forbids overselling. No "eerie", no
  "the network heals itself".
- **Glossary redirect.** The style says to append vocabulary to `GLOSSARY.md`
  at the repo root. **Do not create that file.** New terms go to
  `docs/05-glossary.md`, under a dated heading, appended in the order they came
  up. Two glossaries would eventually mean two definitions of one term.

## The extraction loop

1. Andrey finishes a paper and says so.
2. Claude reads the source — URL or local copy, not memory.
3. The pass produces: new or updated concept/method pages · an updated source
   card · candidate terms for `docs/05-glossary.md` · any project-level open
   question, proposed for `docs/04-decisions.md`.
4. Claude shows the diff, **especially edits to existing pages** — that is
   where a second paper quietly contradicts the first, which is the most
   valuable thing this structure can surface.
5. Andrey corrects. Commit.

---

## Index

### Concepts

| Page | Status | First needed | Sources |
|---|---|---|---|
| [circuit](concepts/circuit.md) | drafted | R0 | olah-2020, elhage-2021, wang-2022, miller-2024 |
| [feature](concepts/feature.md) | drafted | R0 | olah-2020 |
| [polysemanticity](concepts/polysemanticity.md) | drafted | R0 | olah-2020 |
| [superposition](concepts/superposition.md) | stub | R0 | olah-2020 |
| [universality](concepts/universality.md) | drafted | E6 | olah-2020 |
| [circuit-motif](concepts/circuit-motif.md) | drafted | E5 | olah-2020 |
| [interpretability-as-natural-science](concepts/interpretability-as-natural-science.md) | drafted | R1 | olah-2020 |
| [induction-head](concepts/induction-head.md) | drafted | E2 | olsson-2022, elhage-2021, wang-2022 |
| [in-context-learning](concepts/in-context-learning.md) | drafted | E2 | olsson-2022 |
| [phase-change](concepts/phase-change.md) | drafted | E6 | olsson-2022 |
| [qk-ov-circuits](concepts/qk-ov-circuits.md) | drafted | R0 | elhage-2021, olsson-2022 |
| [residual-stream](concepts/residual-stream.md) | drafted | E1 | elhage-2021 |
| [attention-head](concepts/attention-head.md) | drafted | E1 | elhage-2021 |
| [attention-head-composition](concepts/attention-head-composition.md) | drafted | E2 | elhage-2021, olsson-2022, wang-2022 |
| [ioi-circuit](concepts/ioi-circuit.md) | drafted | E1 | wang-2022, miller-2024 |
| [self-repair](concepts/self-repair.md) | drafted (phenomenon) | E4 | wang-2022 |

### Methods

| Page | Status | First needed | Sources |
|---|---|---|---|
| [feature-claim-evidence](methods/feature-claim-evidence.md) | drafted | E3 | olah-2020 |
| [pattern-preserving-ablation](methods/pattern-preserving-ablation.md) | drafted | E1 | olsson-2022, elhage-2021, wang-2022, miller-2024 |
| [head-activation-evaluators](methods/head-activation-evaluators.md) | drafted | E2 | olsson-2022, wang-2022 |
| [path-expansion](methods/path-expansion.md) | drafted | E1 | elhage-2021, wang-2022 |
| [weight-statistics](methods/weight-statistics.md) | drafted | E2 | elhage-2021, wang-2022 |
| [ablation-methodology](methods/ablation-methodology.md) | drafted | E1 | miller-2024, wang-2022 |
| [path-patching](methods/path-patching.md) | drafted | E1 | wang-2022, miller-2024 |
| [activation-patching](methods/activation-patching.md) | drafted | E2 | wang-2022, miller-2024 |
| [mean-ablation](methods/mean-ablation.md) | drafted | E1 | wang-2022, miller-2024 |
| [zero-ablation](methods/zero-ablation.md) | drafted | E1 | wang-2022, miller-2024 |
| [resample-ablation](methods/resample-ablation.md) | drafted | E1 | miller-2024 |
| [circuit-validation-criteria](methods/circuit-validation-criteria.md) | drafted | E2 | wang-2022, miller-2024 |
| [logit-difference](methods/logit-difference.md) | drafted | E1 | wang-2022, miller-2024 |

### Sources

| Key | Phase | Extraction |
|---|---|---|
| [olah-2020](sources/olah-2020-zoom-in.md) — Zoom In | R0 | complete |
| [olsson-2022](sources/olsson-2022-induction-heads.md) — Induction Heads | R0 | complete |
| [elhage-2021](sources/elhage-2021-framework.md) — Mathematical Framework | R0 | complete |
| [wang-2022](sources/wang-2022-ioi.md) — IOI circuit | R1 | complete |
| [miller-2024](sources/miller-2024-faithfulness.md) — Faithfulness metrics not robust | R1 | complete |

### Expected next

**Both required R1 sources are extracted** (Wang et al. and Miller et al.,
2026-09-19). What remains for R1 is not a wiki task: the author's review of
`docs/01-methods.md` against these pages (D-010 item 2) and the R1
resolutions (D-010 item 3). ROME, causal scrubbing and Makelov et al. are
skims and do not gate.

What the Miller pass did to earlier pages:

- **[[ablation-methodology]] is now the frame.** Miller et al.'s six-tuple
  (granularity · component type · value · positions · direction · set)
  places every ablation page here: zero / mean / resample are one axis,
  path patching is edge resample ablation, positions are O-013, direction
  is the necessity/sufficiency split. Every earlier page now cites it.
- **The O-011 trigger fires half.** Path restriction as *edge vs node* is
  first-class in the faithfulness literature and moves IOI faithfulness
  from 87% to a median over 100%. Attention-*pattern* freezing is absent
  from the taxonomy. Recorded on [[pattern-preserving-ablation]]; addendum
  proposed on O-011.
- **[[circuit-validation-criteria]]** carries the robustness result the
  methods doc paraphrases, now from the source: edge vs node, mean vs
  resample, positions, ABBA/BABA, mean set size, averaging order,
  per-prompt spread. Also the Tracr argument that the ground truth itself
  depends on the ablation value, which lands on [[circuit]].
- **[[mean-ablation]]** records Wang et al.'s reference size as "around
  seven examples per template", second-hand from Miller. The methods doc's
  mechanism for the set-size effect is *not* in Miller's text; flagged.
- **[[zero-ablation]]** is drafted, no longer a stub: it has a stated
  question ("include the mechanism that decides it needs to output a
  name").
- **[[activation-patching]]** has the direction × set table (Table 3),
  which is the source for the sufficiency/necessity direction distinction.

**Contradiction log, R1:** none between Wang and Miller as such — Miller
re-measures Wang and both are right about their own six-tuple. The
conflicts are between the wiki's *earlier* framing and the sources:
"direct effect" (O-011 resolution vs Wang), "pattern freezing as a third
axis" (O-011 vs Miller's taxonomy), and "activation patching tests
sufficiency" (glossary vs both).
