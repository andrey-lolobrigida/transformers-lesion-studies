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
  pages; R1 still means rewriting `docs/01-methods.md` yourself. Read the wiki
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
| [circuit](concepts/circuit.md) | drafted | R0 | olah-2020, elhage-2021 |
| [feature](concepts/feature.md) | drafted | R0 | olah-2020 |
| [polysemanticity](concepts/polysemanticity.md) | drafted | R0 | olah-2020 |
| [superposition](concepts/superposition.md) | stub | R0 | olah-2020 |
| [universality](concepts/universality.md) | drafted | E6 | olah-2020 |
| [circuit-motif](concepts/circuit-motif.md) | drafted | E5 | olah-2020 |
| [interpretability-as-natural-science](concepts/interpretability-as-natural-science.md) | drafted | R1 | olah-2020 |
| [induction-head](concepts/induction-head.md) | drafted | E2 | olsson-2022, elhage-2021 |
| [in-context-learning](concepts/in-context-learning.md) | drafted | E2 | olsson-2022 |
| [phase-change](concepts/phase-change.md) | drafted | E6 | olsson-2022 |
| [qk-ov-circuits](concepts/qk-ov-circuits.md) | drafted | R0 | elhage-2021, olsson-2022 |
| [residual-stream](concepts/residual-stream.md) | drafted | E1 | elhage-2021 |
| [attention-head](concepts/attention-head.md) | drafted | E1 | elhage-2021 |
| [attention-head-composition](concepts/attention-head-composition.md) | drafted | E2 | elhage-2021, olsson-2022 |

### Methods

| Page | Status | First needed | Sources |
|---|---|---|---|
| [feature-claim-evidence](methods/feature-claim-evidence.md) | drafted | E3 | olah-2020 |
| [pattern-preserving-ablation](methods/pattern-preserving-ablation.md) | drafted | E1 | olsson-2022, elhage-2021 |
| [head-activation-evaluators](methods/head-activation-evaluators.md) | drafted | E2 | olsson-2022 |
| [path-expansion](methods/path-expansion.md) | drafted | E1 | elhage-2021 |
| [weight-statistics](methods/weight-statistics.md) | drafted | E2 | elhage-2021 |

### Sources

| Key | Phase | Extraction |
|---|---|---|
| [olah-2020](sources/olah-2020-zoom-in.md) — Zoom In | R0 | complete |
| [olsson-2022](sources/olsson-2022-induction-heads.md) — Induction Heads | R0 | complete |
| [elhage-2021](sources/elhage-2021-framework.md) — Mathematical Framework | R0 | complete |

### Expected next

**R0's reading is complete.** Elhage et al. 2021 was extracted 2026-09-14: the
[qk-ov-circuits](concepts/qk-ov-circuits.md) stub was rewritten rather than
extended, as predicted, and `residual-stream`, `attention-head` and
`attention-head-composition` opened. What remains for R0 is not a wiki task —
it is the exit note in `notes/exit_criteria/R0.md`, written cold, and then the
diff against these pages.

Two things the Elhage pass did to earlier pages, which is the kind of edit the
loop exists to surface:

- **[induction-head](concepts/induction-head.md)** gained the mechanism from
  its original source and the exact wording of the GPT-2 pointer-arithmetic
  observation — "at least one case in GPT-2", no size. That did not resolve
  the page's first open question; it sharpened it into O-012.
- **[pattern-preserving-ablation](methods/pattern-preserving-ablation.md)** had
  described Elhage et al.'s ablation at second hand; the description is now
  from the source and the freezing trick has its 2021 provenance.

No contradiction between sources yet. The composition page records a
*self*-correction inside Elhage et al. (the Frobenius-norm bug) which is the
nearest thing so far.

The `concepts/` vs `methods/` boundary needed one judgment call: the eigenvalue
copying statistic and the composition scores are computed from weights, not
from a forward pass, but they are still *measurements with a licence*, so they
went to `methods/` with a claim-licence block rather than being buried in a
concept page.

**R1 next:** Wang et al. (IOI) and Miller et al. are the first sources that
will press on [pattern-preserving-ablation](methods/pattern-preserving-ablation.md),
[path-expansion](methods/path-expansion.md) and the O-011 resolution.
