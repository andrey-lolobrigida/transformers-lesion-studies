# CLAUDE.md — Lesion Studies for Transformers

*Living document. Update it in the same session a decision is made, not later.*

**Status:** R0, R1 and E0 done (R2 gates E4, R3 later). E0 tagged `v-E0` on 2026-09-20: environment verified, smoke test in `src/lesion/e0_smoke.py`, artifact in `results/E0/`; the published IOI baseline is bracketed, not matched (D-011, O-014).
**Current phase:** E1 (task battery and harness), not yet started. Plan it at the start of its own branch. See `docs/02-roadmap.md`.
**Last updated:** 2026-09-20

---

## Start here

1. Read this file.
2. Read `docs/04-decisions.md` — that's where the live state is.
3. Check the current phase in `docs/02-roadmap.md` and work only on that phase.

Everything else is reference. Don't re-derive it.

## What this project is

Take a small pretrained transformer, disable individual components (attention
heads, neurons, layers), and measure how behaviour degrades across different
tasks. Build a functional map from the damage pattern. This is the lesion-study
method from neuroscience, applied to a system where the intervention is exact,
repeatable, and reversible.

The stated goal is **reproduction-first research**: carefully replicate known
results, then map where they break. Novel findings are welcome when they fall
out of that, but they are not the target. See `docs/00-motivation.md` for the
full framing and for where the neuroscience analogy stops being useful.

The intended spine is **self-repair after ablation, with the mechanical
component controlled for** — see `docs/02-roadmap.md`, phase E4. This is a
lean, not a commitment; it gets confirmed or dropped after E3.

## Hardware and environment

RTX 5060, 8 GB VRAM, Blackwell (sm_120), normal desktop. Local-first.
Everything through E4 runs comfortably. Setup notes and known gotchas:
`docs/06-environment.md`.

## Epistemic rules

These are the point of the project. They are not optional and they are not
stylistic. Most of what separates credible interpretability work from
plausible-sounding noise is discipline about what a given measurement licenses
you to claim.

1. **Never write "head X does Y."** Write "under {ablation method} on
   {dataset}, ablating head X changes {metric} by {amount}." If a sentence in a
   result summary can't be rewritten in that form, it isn't a result yet.

2. **Necessity and sufficiency are different claims.** Ablation tests
   necessity ("does it break without this?"). Activation patching tests
   sufficiency ("does restoring this fix it?"). Never let a necessity result
   get written up in sufficiency language. This confusion is the single most
   common failure mode in this literature.

3. **The ablation defines the task.** Zero-ablation and mean-ablation are not
   crude-vs-refined versions of one measurement — they ask different
   questions. Always run both and report both side by side. If they disagree,
   that disagreement *is* the finding; don't pick the cleaner one.

4. **Record the mean-ablation dataset size, always.** Faithfulness scores are
   known to shift with it, and small samples (single digits) can manufacture
   results. Log the size next to every mean-ablation number.

5. **Logit difference over loss** as the default metric, unless there's a
   written reason to use loss for a specific battery item.

6. **Every number in a result doc needs a rerun command, a seed, and a model
   revision hash.** If it can't be reproduced from the repo in one command, it
   goes in `notes/`, not in results.

7. **A clean, exciting result triggers an adversarial check, not a writeup.**
   Vary the ablation method, the prompt template, and the corruption scheme
   before believing it.

8. **Negative and null results get logged.** `docs/04-decisions.md` has a
   section for them. Deleting a failed experiment destroys the most useful
   information the project produces.

## Working conventions

- **Git as narrative.** One branch per phase (`phase-E3-functional-map`), tag
  on completion (`v-E3`). The diff between phases should be readable as the
  story of the project.
- **Scripts over notebooks** for anything that will be rerun. Notebooks are
  for looking at things once; if it produces a number that ends up in a
  writeup, it lives in `src/` with a CLI.
- **Results are files, not memories.** Every experiment writes a JSON/parquet
  artifact under `results/{phase}/` plus a short `README.md` interpreting it.
- **One idea per note.** `notes/` holds granular reading notes and scratch
  reasoning, `NN-kebab-case.md`, not one growing file.
- **Exit notes are filed apart.** Where a reading phase's exit criterion is
  a cold note (R0; not R1, whose deliverable is the reviewed methods doc,
  D-010), it lives in `notes/exit_criteria/<PHASE>.md` — one file per phase,
  covering all of that phase's criteria. Deliberately not mixed in
  with the numbered reading notes: an exit note is the phase deliverable, is
  written cold and without looking (D-007, D-009), and gets revised until the
  gate passes, whereas a reading note is scratch and is never revised. Same
  reason `notes/` and `wiki/` are separate directories.
- **`notes/` is yours, `wiki/` is the field's.** The wiki is organised by
  concept, built by extracting papers, and is a scaffold — never a substitute
  for an R-phase exit note written cold. Conventions in `wiki/README.md`,
  decision in D-009. New vocabulary goes to `docs/05-glossary.md`; a root
  `GLOSSARY.md` is deliberately never created.
- **Errata policy:** fix forward on `main`, record the correction in
  `ERRATA.md` with the affected phase and commit link. Don't rewrite old
  phase branches.

## Repo layout

```
lesion-studies/
├── CLAUDE.md              ← this file
├── README.md
├── ERRATA.md
├── docs/                  ← reference documents (see below)
├── notes/                 ← reading notes, scratch reasoning (yours)
│   └── exit_criteria/     ← R-phase exit notes, one per phase, written cold
├── wiki/                  ← concept reference built from the papers (D-009)
├── src/                   ← the harness and experiment scripts
├── batteries/             ← task datasets (clean/corrupted pairs + metrics)
├── results/{phase}/       ← experiment artifacts + interpretation
└── writeups/              ← blog-post drafts, figures
```

`docs/` contents:

| File | What's in it |
|---|---|
| `00-motivation.md` | Why this project, the neuroscience framing, where it breaks |
| `01-methods.md` | The methods ladder, corrected; what each measurement licenses |
| `02-roadmap.md` | Reading phases R0–R3, experiment phases E0–E6, exit criteria |
| `03-reading-list.md` | Papers grouped by phase, with why each matters |
| `04-decisions.md` | **Dated decision log + open questions + null results** |
| `05-glossary.md` | Terms |
| `06-environment.md` | Hardware, install order, known gotchas |
| `07-alignment-extension.md` | **Parked.** A possible successor project. Not a plan — do not start before E4 ships |

`wiki/` is documented by its own `README.md`, which is the operating manual
for how papers get extracted into concept pages.

## What Claude should not do here

- **Don't decide the spine, the scope, or the venue alone.** Propose options
  with honest trade-offs; the call belongs to the author.
- **Don't plan future phases in detail.** E5 and E6 are deliberately sketches.
  Detailed planning happens at the start of the phase, not before.
- **Don't invent citations, arXiv IDs, or numbers.** If a reference is
  uncertain, mark it `[unverified]` and say so out loud. A wrong citation in a
  reproduction-first project is worse than no citation.
- **Don't skip the reading phases to get to code.** R0 and R1 exist because
  claims made without them have to be retracted later. Being asked "can we
  just start coding" is not authorisation to skip them — say so.
- **Don't soften a negative result.** If a reproduction fails to reproduce,
  that goes in the log at full strength.
- **Don't oversell.** Sober register throughout: describe what was measured
  and what it does and doesn't show. No "eerie", no "the network heals
  itself", no claims about what this means for AI safety.
- **Don't scale up to escape a problem.** If something doesn't work on GPT-2
  small, a bigger model won't fix it, it will hide it.
- **Don't start the parked alignment extension** (`docs/07`). It's a
  possibility, not a plan. Its activation criteria are listed in the document
  itself; if they're not met, say so rather than sketching experiments.

## Decision log

Lives in `docs/04-decisions.md`. Every structural decision from a session goes
in there dated, with the reasoning, in the same session it's made.
