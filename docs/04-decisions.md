# 04 — Decision log, open questions, null results

**This is the live document.** Everything else is reference. New sessions read
this second, after `CLAUDE.md`.

Decisions get appended dated, with reasoning, in the session they're made.
Superseded decisions are struck through, not deleted — the reasoning trail is
worth more than tidiness.

---

## Decisions

### D-001 — Goal shape: reproduction-first
*2026-08-01*

Three modes were on the table: portfolio showpiece, reproduction-first
research, novelty-hunting. **Chose reproduction-first.**

Reasoning: in an area with documented robustness problems, establishing where a
published result stops holding is a genuine contribution. It also tends to
generate novel questions organically — you reproduce, notice an unturned knob,
turn it — which is a more reliable path to originality than searching for it
directly. Explicitly *not* pressuring toward novelty-hunting.

### D-002 — Spine: self-repair with the mechanical component controlled for
*2026-08-01*

Of the candidate directions, chose the self-repair/backup question, reframed.
Not "does the network heal itself" (partly answered, and partly mundane) but
"how much self-repair survives once LayerNorm rescaling is accounted for, and
what is doing the rest?"

Reasoning: prior work establishes that a substantial share of apparent
self-repair is a mechanical consequence of the architecture rather than learned
compensation, and reports an unexplained residual. That residual is a concrete
target, it's cheap on this hardware, and it fits the reproduction-first mode.

**Status: lean, not commitment.** Confirmed or replaced after E3, and gated on
R2 confirming the gap is still open (see O-001).

### D-003 — Units of analysis: heads, not SAE features
*2026-08-01*

Reasoning: the feature-level direction is real but is a different project with
a different tooling burden, and it means competing directly with
well-resourced labs on their release cadence. Heads are well-documented, have
published numbers to check against, and fit the reproduction-first goal. The
comparison between head-level and feature-level lesions is interesting and
deferred, not rejected.

### D-004 — Rigour: patching from the reproduction phase onward
*2026-08-01*

Activation patching enters at E2, not later. Reasoning: the whole value of the
reproduction-first mode is not having to walk back claims. Ablation-only
results in E2 would need re-verification anyway.

### D-005 — Drop arithmetic from the task battery
*2026-08-01*

GPT-2 small does not do arithmetic well enough for lesion results to be
distinguishable from noise. Included in the original brainstorm; removed.

### D-006 — Report zero, mean, and resample ablation together, always
*2026-08-01*

Not as robustness theatre — because they ask different questions. Following
Miller et al., the ablation methodology partly defines the task being measured.
Disagreement between methods is treated as a result to investigate.

### D-007 — Reading phases are hard gates
*2026-08-01*

R1 gates E1; R2 gates E4. No code during R phases. Reasoning: this is the
mechanism that makes D-001 real rather than aspirational.

### D-008 — Alignment extension: parked, documented, not scheduled
*2026-08-01*

An alignment-flavoured successor project was discussed and written up in
`docs/07-alignment-extension.md`. **Parked, not adopted.**

Reasoning: the methods transfer cleanly — refusal ablation is already a lesion
study — but the extension depends on having a validated harness and calibrated
habits, both of which are outputs of the core project. Starting there first
means fuzzy metrics measured with unvalidated tooling. Documented now so the
reasoning isn't lost; activation criteria are listed in the doc.

### D-009 — Reading phases produce a concept-first wiki
*2026-08-30*

Papers are extracted into concept pages under `wiki/`, not summarised one page
each. `wiki/concepts/` is what a thing is, `wiki/methods/` is what you do to it
and carries a mandatory claim-licence block; `wiki/sources/` holds a thin
bibliographic card per paper with no summary prose.

Reasoning: the wiki is a **scaffold, not a substitute**. R-phase exit criteria
are unchanged — the R0 note is still written cold and without looking, and the
diff against the wiki page is the diagnostic. Concept-first makes that
structural rather than a rule to remember: with no per-paper summary page in
existence, nothing is shaped like the note that has to be written from memory.
Pages are written from the actual source text, never recall — Claude's training
data ends around May 2026, so `arXiv 2607.01940` is outside it entirely.

Two consequences worth recording separately:

- **Glossary stays single.** The `curious-student` output style appends new
  vocabulary to `GLOSSARY.md` at the repo root. That file is deliberately never
  created; terms go to `docs/05-glossary.md`. Two glossaries means two
  definitions of one term.
- **R phases get branches too.** `CLAUDE.md`'s one-branch-per-phase convention
  now covers reading phases: `phase-R0-orientation`, tagged `v-R0` at exit.

Operating manual in `wiki/README.md`. Full design record is local-only in
`.superpowers/specs/2026-08-30-concept-wiki-design.md` (untracked, so this entry
is the durable record).

---

## Open questions

### O-001 — Has recent work closed the E4 gap?
`arXiv 2607.01940` (Conditional Co-Ablation, ~July 2026) works on recovering
self-repair-masked backups and validates on the GPT-2 IOI backup heads.
**Resolve during R2.** If it has closed the specific residual E4 targets, E4
gets redesigned. Possible fallbacks: the ablation-method-dependence of the
mechanical/residual split, or extending to Pythia for a cross-model version.

### O-002 — Venue and format
Blog post plus repo is the default and is sufficient. BlackboxNLP is the
plausible workshop target if E4 produces something. **Not deciding now** — the
decision changes what E4 needs to report, so defer until E4's shape is known.
Deliberately not chasing MIB comparability unless it falls out for free.

### O-003 — Does the corruption scheme need to vary too?
The ablation method defines the task; the corruption scheme in patching
plausibly does the same. Should E2/E3 sweep corruption schemes the way they
sweep ablation methods, or is that scope creep? **Resolve during R1.**

### O-004 — Pythia viability for E6
Do Pythia 70M/160M form clean induction heads at all? Are the early checkpoints
dense enough in the formation window? Deduped or non-deduped? **Resolve if and
when E6 is planned** — not before.

### O-006 — Should knock-in calibration be pulled forward?
The one piece of `docs/07` that might belong in the core project: train a small
model with a deliberately planted mechanism, then check whether the E1 harness
recovers it. Ground truth by construction, which is otherwise unavailable — it
would turn "our numbers match the literature" into a controlled test of what
the E3 heatmaps are actually worth. **Resolve at the E4 retrospective**, not
before; it's a real scope increase and the core project is complete without it.

### O-005 — Is the E4 residual large enough to study?
After removing the mechanical LayerNorm share, the remaining self-repair may be
small and noisy. This is a real risk to the spine. **Resolve in E4 itself**; a
small residual is a publishable negative result but changes the writeup
substantially.

---

## Null and negative results

*Nothing yet. Anything that fails to reproduce, fails to replicate, or comes
out null goes here at full strength with a link to the results artifact.
Deleting these destroys the most useful information the project produces.*

| Date | Phase | What was expected | What happened | Artifact |
|---|---|---|---|---|
| — | — | — | — | — |
