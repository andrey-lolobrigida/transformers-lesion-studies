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

### D-010 — R1 exit criterion: review the methods doc, don't rewrite it
*2026-09-19*

The roadmap's R1 exit criterion was to rewrite `docs/01-methods.md` cold,
replacing the draft. Replaced. R1 now exits when all three hold:

1. Wang et al. 2022 (IOI) and Miller et al. 2024 (faithfulness metrics) are
   extracted into the wiki. ROME, causal scrubbing and Makelov et al. stay
   skims or conditional reads and do not gate.
2. `docs/01-methods.md` has been reviewed by the author against those pages
   and edited wherever it is wrong or missing, in a commit the author makes.
   The draft was written in August before any paper was extracted and has not
   yet been checked against a source.
3. Every item pinned to R1 is resolved or explicitly deferred with a reason:
   O-003 (sweep corruption schemes?), O-007 (MLPs first-class?), O-011's R1
   trigger (pattern freezing as a third axis?), the reconciliation of the
   wiki's structural circuit definition with the glossary's behavioural one,
   and whether Miller et al. contradicts
   `wiki/methods/pattern-preserving-ablation.md`.

Reasoning: the author had already read both required papers and judged the
draft better worded than a cold rewrite would be. Writing cold was R0's
mechanism for testing recall; the methods doc is not a recall test but the
reference that prevents sloppy claims in E3 and E4, so correctness matters
more than authorship. What the gate actually protects is that E1's harness
design is not fixed before the methods questions are settled, and that part
is kept. D-007 stands: no code during R1.

Consequence for the exit-note convention: `notes/exit_criteria/<PHASE>.md`
is for phases whose criterion is a cold note. R1's deliverable is the edited
methods doc itself, so there is no `R1.md`.

Option considered and rejected: removing the gate entirely so E1 could start
at will. The risk was that the harness would bake in an answer to O-007 or
O-011 by default rather than by decision.

*Status 2026-09-19.* Item 1 done (both extractions committed or pending
commit). Item 3: O-003 resolved, O-011's R1 trigger resolved, O-013
resolved (all below); O-007 resolved 2026-09-20 after the ROME skim; the circuit-definition reconciliation and the
Miller-vs-pattern-preserving question are answered on
`wiki/concepts/circuit.md` and `wiki/methods/pattern-preserving-ablation.md`
and await the author's sign-off as part of item 2.

#### Closed — *2026-09-20*

All three items hold. **Item 2:** the author reviewed `docs/01-methods.md`
against the wiki and edited it in commit `b307396` (metric definitions
added; direction qualifier on activation patching; the unsourced
mean-set-size mechanism withdrawn; causal-tracing paragraph corrected for
windows and metric). **Item 3, last two:** the circuit-definition
reconciliation is **accepted as written** — two named senses, a
*structural* circuit read off parameters (Olah et al., Elhage et al.) and
a *behavioural* circuit that is a component subgraph plus the ablation
six-tuple defining its function (Wang et al., Miller et al.), with every
results doc stating which sense a claim is about; glossary updated. The
Miller-vs-pattern-preserving question was answered by the O-011 R1
trigger resolution (2026-09-19): no contradiction, pattern freezing is
this project's own axis with no faithfulness-literature backing, recorded
as such. R1 tagged `v-R1`. Per the dependency diagram E1 is gated on R1
*and* E0; E0 (environment and smoke test) is the next phase.

### D-011 — E0 outcome: the published IOI baseline is bracketed, not matched
*2026-09-20. Proposed by Claude from the E0 run; confirmed by the author the
same day, with the reported-vs-released dataset discrepancy named as the
deciding consideration. E0 tagged `v-E0`.*

E0's exit criterion is "one command in the repo reproduces one published
number". The number chosen was Wang et al.'s clean mean logit difference on
`p_IOI`, **3.56 over 100,000 samples** [wang-2022 §2]. The command is
`uv run python -m src.lesion.e0_smoke --n 100000 --seed 0`; the artifact is
`results/E0/e0_smoke_seed0_n100000.json` (interpretation in
`results/E0/README.md`).

What the run gives, GPT-2 small at HF revision `607a30d7`, 100,000 prompts
drawn from the released templates and word lists, seed 0:

| Tokenisation | Templates | Mean logit diff | IO over S | IO prob |
|---|---|---|---|---|
| no BOS (released code's default) | all 15 × 2 orders | 3.648 ± 0.005 | 99.4% | 52.7% |
| no BOS | first 7 × 2 orders (the released code's `mixed` mode with its default count) | 3.485 (derived from per-template means) | — | — |
| BOS prepended (TransformerLens default) | all 15 × 2 orders | 3.922 ± 0.006 | 98.9% | 52.0% |
| *published* | *"15 templates", "mixed"* | *3.56* | *99.3%* | *49%* |

So the published number is **not matched at two decimals** by any procedure
this repo can justify, and it **is bracketed** by the two readings of the
template mix that the paper text and its code leave open, both without BOS.
The BOS tokenisation is excluded: it overshoots by 0.36, seventy standard
errors. Two facts block an exact match and cannot be resolved from the
sources: the released word lists (99 names, 8 places, 8 objects) differ from
the paper's stated 100/20/20, and the repository history begins after the
paper's v1 (see the gotcha log in `docs/06-environment.md`).

**Decision:** treat E0's gate as passed on the strength of (a) the
environment working end to end with determinism verified, and (b) the
published baseline reproduced to within the spread of the paper's own
under-specified design choices, with the gap logged as a null result below
rather than explained away. The alternative — chasing 3.56 by tuning the
template mix until it lands — would be fitting to the answer and is
declined. **Consequence for E1/E2:** every IOI number this project checks
against Wang et al. carries the same ±0.1 design-choice uncertainty; E2
should compare *changes* under intervention, not absolute levels, and should
say so.

Recorded in the same session: `prepend_bos` is a first-class knob of every
future IOI measurement, reported both ways until one is chosen with a
written reason (O-014).

### D-012 — E1 is split into E1a (harness) and E1b (battery)
*2026-09-20. Proposed by the author at the E1 kickoff; the sub-phase shape
and exit criteria proposed by Claude and confirmed the same session.*

The roadmap's E1 bundled two subsystems that share only a prompt-pair
interface: the intervention harness, and the four battery items. They are
split into two sub-phases, each with its own branch and tag, run in order.

**E1a — harness.** Branch `phase-E1a-harness`, tag `v-E1a`. Exit
criterion: the harness half of the former E1 criterion, verbatim — one CLI
call ablates an arbitrary head or MLP layer under all three substitution
values, at node or edge level, with any position mask, with or without
pattern freezing, every setting recorded in the artifact. Validated on IOI
only, which is the one battery item that already exists, with two checks:
an identity intervention reproduces the E0 clean baseline bitwise, and
mean-ablating MLP0 on `p_ABC` reverses the sign of the mean logit
difference, as Wang et al. report [wang-2022 App. J]. That second check is
a published intervention number and would ordinarily be E2's job; it stays
in E1a because a harness that cannot bracket one known effect on the one
dataset already held is exercised, not validated. E1a states the bracket,
not a match, for the reasons in D-011.

**E1b — battery.** Branch `phase-E1b-battery`, tag `v-E1b`. Exit
criterion: the battery half of the former criterion — every item has a
clean/corrupted generator, a metric with its expected direction under damage
(O-009 addendum), and a documented corruption scheme stating what it removes
and what it inserts (O-003). O-009 resolves here, including whether a
control item enters for a noise floor. E2 is gated on `v-E1b`.

Reasoning: a single spec covering both halves is long enough that the
battery half gets the least review, and the battery questions (agreement
dataset, factual-recall corruption and filter, induction metric, control
item) are the ones most likely to change once the harness produces its first
numbers. Sequencing harness first means every later item is measured with a
validated instrument, so a strange reading on a new item cannot be blamed on
the harness. Cost: one extra tag, this entry, and the roadmap edit made in
the same session.

Option considered and rejected: one phase with the harness built first and
the items following on the same branch. Same order, but the IOI validation
would have had no gate of its own.

*2026-09-20, E1a validation.* Harness built as specified in the E1a design
(hand-rolled on TransformerLens hooks; both directions; per-run mean
references; freeze plus edge refused; parquet per prompt, zstd-compressed —
`pyarrow` reads it without ceremony). Check 1 (identity with E0) passed
bitwise on the 100,000-prompt run at batch size 512; that run fits the 8 GB
card because the runner frees the clean and ablated per-batch logit tensors
at the end of each batch rather than holding three alive across the loop
boundary (`src/lesion/runner.py`, commit `db460d0`). Check 3 (determinism)
passed. Check 2 (MLP0 bracket) outcome per value is in
`results/E1a/README.md` and the row below.

### D-013 — E1b shape; subject–verb agreement becomes a fallback item
*2026-09-23, at the E1b kickoff. Shape and fallback proposed by Claude;
confirmed by the author the same session.*

**Shape.** E1b is one spec. It settles the cross-cutting rules first (the
clean-accuracy gate, the control item, the expected-direction field, any
generalisation of `PromptPair`), then gives each item a short section of its
own. Items are built in order of how much they strain the E1a battery
interface, least first, so a protocol change shows up on an easy item: IOI
App. A extras → induction → factual recall. One branch
(`phase-E1b-battery`), one tag (`v-E1b`), as in D-012.

**Subject–verb agreement leaves the default battery.** The roadmap listed
it as a fourth item. It is the only item with no source on the reading list,
so every choice would be ours: noun list (plural forms often tokenise to a
different length than the singular, which breaks pair alignment), tense,
subject–verb distance, attractor nouns. Each of those changes what the item
measures, and there is no published number to check against. Its marginal
contrast on the E3 map is also the lowest of the four: IOI, induction and
factual recall already cover name routing, token copying and retrieval. Adding
references to source it was considered and declined (the reading list stays as
it is for now).

**Fallback rule.** Agreement comes back only if factual recall fails its
clean-accuracy gate or passes it with too few surviving prompts (the
threshold is set with the gate rule, in the E1b spec). The reason is
contrast: without factual recall the battery is IOI plus induction, and those
overlap mechanistically (the IOI circuit contains induction heads 5.5 and
6.9 [wang-2022 §3.3]), so the E3 map would have little to compare. If it
comes back, it enters as an explicitly **unsourced** item. The spec and
results README say it departs from reproduction-first and that no published
number exists for it. If factual recall passes, agreement stays out and this
entry records it as dropped.

Options considered and rejected: a short reading pass to source agreement
(declined, so the reading list doesn't grow), and building it unsourced
unconditionally (not worth the unanchored design choices unless the battery
needs the contrast).

*Outcome, 2026-09-23:* factual recall **failed** its pre-registered gate
(`subject_swap`, n=64 = every admitted survivor, seed 0, no BOS;
`uv run python -m src.lesion.e1b_gate --item all`): pairwise accuracy 1.000
against 0.90 (pass), gap +4.104 ± 0.374 logits against 1.0 (pass), admitted
survivors 64 against 300 (fail). The ROME known-facts filter re-run on
GPT-2 small, plus the partner requirement (ours), left 1,965 survivors spread over 672 templates, of which 2 reach
the per-template floor of 30. **The fallback is triggered; the agreement
addendum is pending the author.** Numbers and the survivor funnel:
`results/E1b/README.md` §3–4; null-results row below.

*Agreement addendum, 2026-09-24.* Proposed by Claude
(`.superpowers/specs/2026-09-24-e1b-agreement-addendum.md`), every
recommendation accepted by the author the same session. Agreement is built
under the unchanged D-014 gate (pairwise accuracy ≥ 0.90, gap ≥ 1.0 logit,
seed 0, n = 2,000), thresholds fixed here, before the generator runs. All
choices are ours; no published number is checked against the item.

1. **Nouns:** about 40 animate common nouns with regular `-s` plurals; a noun
   is kept only if singular and plural are each one token (enforced by the
   generator, pinned by a fast-tier test). Irregular plurals are out.
2. **Verbs:** `is`/`are` and `has`/`have`, present tense, drawn per prompt.
   The verb is not in the prompt; it only picks the two logits `ld` reads
   (`c` = the agreeing form, `s` = the other form of the same verb).
3. **Structure:** `The {N1} {prep} the {N2}` → verb, `prep` ∈ {`near`,
   `behind`, `beside`, `with`}; one fixed length.
4. **Attractor:** `N2` shares `N1`'s number or not, 50/50; congruency is in
   the template key (8 templates: preposition × congruency); subject number
   is not. The gate reads the pooled default; per-congruency readings are
   logged, ungated.
5. **Default corruption `number_flip`:** `N1` replaced by its other-number
   form. Expected fraction removed ≈ 2 (cited per D-014 item 2); it turns
   congruent prompts into incongruent ones and back. Keeping subject number
   out of the template key keeps each template's mean-ablation reference
   number-balanced. Extra: `number_flip_all` (`N1` and `N2` flipped), ungated.
6. **BOS prepended** by default; **no prompt filter** (D-014 item 3).
7. **If agreement fails its gate:** the null is logged at full strength and
   E3 runs on IOI and induction, stating the overlap this entry names. No
   threshold relaxation and no re-cut of templates.

*Wording correction.* "No published number exists for it" above overstates
what was checked. Agreement has a literature, including work on GPT-2
[unverified: Linzen, Dupoux & Goldberg 2016; Finlayson et al. 2021]. Neither
is on the reading list. Read the sentence as "no source on the reading list,
so no published number is checked against it". The fallback is unchanged.

*Agreement outcome, 2026-09-24:* agreement **passed** its pre-registered gate
(`number_flip`, n = 2,000, seed 0, BOS prepended;
`uv run python -m src.lesion.e1b_gate --item agreement`, at `718ec4b`):
pairwise accuracy 0.983 against 0.90 (pass), gap +5.169 ± 0.041 logits
against 1.0 (pass). Fraction removed 1.98, near 2 as expected by design (item 5); measured, not
guaranteed.
The failure branch of item 7 is not triggered; agreement stays in the
battery as the fallback, unsourced and ours. Noise floor measured
(`uv run python -m src.lesion.e1b_noise --item agreement`). Numbers, the
ungated breakdown and the noise floor: `results/E1b/README.md` §3, §7, §10.
The build choices the addendum left open are listed in the agreement plan
and are pending the author's ruling; none is recorded here yet.
*(Superseded by the balanced-draw rerun below; numbers kept as the record of
the first run.)*

*Agreement: draws balanced per template, 2026-09-24.* Decided by the author
after the first gate and noise run. The generator no longer draws
preposition, congruency and subject number independently (50/50 for the last
two, so balanced in expectation only); prompts now come in blocks of 16, each
block one shuffle of every (preposition, congruency, subject number) cell, so
at n a multiple of 16 each template `{prep}/{congruency}` has exactly n/8
prompts, half singular and half plural; the verb pair is still drawn per
prompt (`src/lesion/agreement.py`, `803ec36`). This settles "how draws are
made", one of the build choices the addendum left open; the others are still
pending. Reason: the first run's largest noise floor, 0.2977 on L0.mlp, came
from the reference-seed spread (sd 0.2977 against sem 0.0608), with
`effect_mean` +0.856 to +1.494 across ref seeds 0–4. A reviewer's scratch
check (five reference seeds, not a repo artifact, not a result) found that
L0.mlp's `effect_mean` followed each reference draw's plural fraction: seeds
2, 1, 3, 0, 4 had plural fractions 0.479, 0.488, 0.488, 0.519, 0.520 and
`effect_mean` 0.86, 0.91, 0.98, 1.49, 1.41; that is five points. First run: gate at `718ec4b`
(artifacts in `17cb218`), `number_flip` PASS, pairwise accuracy 0.983, gap
+5.169 ± 0.041; noise floor in `e460d90`. Rerun
(`uv run python -m src.lesion.e1b_gate --item agreement`, n = 2,000, seed 0,
BOS prepended, at `803ec36`, artifacts in `5a53407`): `number_flip` **PASS**,
pairwise accuracy 0.981 against 0.90, gap +5.141 ± 0.040 logits against
1.0, fraction removed 2.00; every template has exactly 250 reference prompts
at ref n = 2,000. Rerun noise floor
(`uv run python -m src.lesion.e1b_noise --item agreement`, ref n = 2,000,
ref seeds 0–4, at `5a53407`, committed in `7d25f69`): largest floor 0.0537
on L0.mlp, where the sem dominates (sem 0.0537 against reference-seed sd
0.0425); the sem dominates all 24 components. The gate rule and its
thresholds (D-014 item 1) did not change. The failure branch of item 7 is
not triggered. Details and the side-by-side L0.mlp rows:
`results/E1b/README.md` §7, §10.

*Agreement build choices accepted, 2026-09-24.* The E1b agreement plan made
nine choices the addendum left open; the author accepted them as built
(choice 3 was replaced, as above).

1. The candidate noun list is 50 words chosen by Claude, animals, occupations
   and people with regular `-s` plurals. 46 are kept on the pinned GPT-2
   tokenizer; `owl`, `eagle`, `baker` and `painter` drop because their
   plurals are two tokens.
2. N1 and N2 are always different nouns.
3. Replaced by exact per-template balance (paragraph above).
4. The labels are `N1`, `PREP`, `N2` and `END`, with `END` = `N2`'s index.
   Sentence-initial `The` carries no leading space; ` the` does.
5. The corruption draws no random numbers, so both schemes share one clean
   stream at a given seed.
6. The gate records an ungated per-value `breakdown` for the keys a battery
   names in an optional `breakdown_keys` attribute, read with `getattr` so the
   `Battery` protocol does not change. Agreement names `congruency`, `verb` and
   `subject_number`. The last was added by the plan to separate a
   number prior from agreement.
7. Only `--item agreement` was run. The other items' gate artifacts were not
   regenerated, and they carry no `breakdown` field.
8. The README section is appended as §10, so earlier section numbers do not
   move.
9. The fast tier stays offline. The noun-list check against the real
   tokenizer is a slow test.

Also noted and accepted without action: on the gate prompts the agreeing verb
is rarely the clean top-1 token (top-1 rate 0.060, mean P[c] 0.032), so `ld`
on this item reads as a two-form preference conditional on a verb of the drawn
pair, not as what the model generates (`results/E1b/README.md` §10).

### D-014 — E1b battery rules: the gate, the noise floor, the interface
*2026-09-23, E1b design. Proposed by Claude, each point confirmed by the
author the same session. Item-level detail lives in the E1b spec; this
entry records what outlives the phase.*

1. **Every item passes a clean-accuracy gate before E3**, on its default
   corruption scheme, with thresholds fixed before any generator runs:
   pairwise accuracy `1[logit[c] > logit[s]]` ≥ 0.90; clean-minus-corrupt
   mean logit difference ≥ 1.0 logit; for factual recall, ≥ 300 surviving
   prompts in admitted templates. None is a published value. A failure is a
   null result at full strength, and thresholds are not relaxed after seeing
   numbers. Named extras are not gated.
2. **The gap condition is absolute, not a ratio.** A 50% share-of-signal
   floor was proposed and dropped by the author: partial removal is
   sometimes what a scheme is for (Wang's App. A), and what a small gap
   harms depends on its absolute size against its standard error. Instead,
   **every later mean- or resample-ablation number carries the fraction of
   the clean logit difference its reference scheme removes**, beside the
   reference size rule 4 already requires.
3. **Only factual recall filters prompts** (ROME's known-facts rule, re-run
   on GPT-2 small); IOI and induction keep their sources' unfiltered
   populations.
4. **Every item names a competitor token and declares an expected
   direction** (`positive` for all three: damage lowers `ld`). The direction
   is for the item, not a prediction per component.
5. **A template enters a mean-ablation run only with ≥ 30 reference
   prompts** (anchor: E1a's IOI numbers rest on ≈ 33). Reported by the E1b
   gate, not enforced by the harness, so E1a stays reproducible.
6. **Items fit the E1a interface; it is generalised only when forced**, and
   each forced change is logged. None was forced in design. Consequences:
   induction reads one position per prompt; factual recall uses a subject
   swap (competitor: CounterFact's `target_new`) rather than ROME's embedding
   noise, which is deferred because it would change `interventions.py`.

### D-015 — E2 rules: what "matched" means, and what the targets run on
*2026-09-29, E2 design. Proposed by Claude, each point confirmed by the
author the same session; the spec was approved the same day. Target-level
detail lives in the E2 spec
(`.superpowers/specs/2026-09-29-e2-reproduction-design.md`, untracked); this
entry records what outlives the phase.*

1. **Shape.** One phase, shaped like E1b: the shared rules first, then
   induction (I1–I4), then IOI (P1–P4). One branch
   (`phase-E2-reproduction`), one tag (`v-E2`). Rejected: an E2a/E2b split,
   which would pin the matching rule and the new machinery before IOI had
   exercised them.
2. **Verdicts.** Each target gets one of: `matched` / `not matched` (a
   published number or identity exists); `bracketed, uninformative` (a
   magnitude whose bracket contains its contrast value); `measured` (no
   published GPT-2 small counterpart). A verdict is written only at
   pre-registered settings; the constants are committed before the first
   GPU run.
3. **Identity rule.** Rank every candidate sender by the class's own score,
   receiver included. The class matches iff every published member is in
   the top `k = max(class size + 2, the rank the source itself states)`, so
   the rule is never stricter than the source. Negative classes rank from the
   bottom. A tie straddling the cut counts as inside and is reported.
4. **Sign rule.** Published sign **and** `|effect| > max(2 × sem, the item's
   largest E1b noise floor)`. A published null matches iff the effect stays
   inside that bound; the results doc says that matching a null shows only
   that we also found nothing.
5. **Magnitude rule.** A bracket over the settings the source leaves open.
   For IOI there are four corners: {15, 7} templates per order ×
   {≈ 7 per template, 2,000 total} mean-reference prompts. The ≈ 7 corner is
   Miller et al.'s reading of Wang et al., who do not state it. It breaks
   D-014's floor of 30, is labelled as doing so, and never stands alone.
   Each quantity names a **contrast value**, an alternative that would change
   the claim. A bracket that contains the contrast value is `bracketed,
   uninformative`. Otherwise the verdict is `matched` if the published value
   is inside, and `not matched`, at full strength, if it is outside. The width
   is always reported. Rejected: a fixed band per quantity (a number chosen
   with nothing behind it); statistical agreement alone (E0's baseline sat
   seventeen standard errors off while inside the bracket).
6. **D-006 inside a reproduction.** Verdicts are written at the source's
   substitution value only. The other two values run beside every gated
   number, ungated, in the same table.
7. **Downstream targets run on the published head lists, verbatim**, whatever
   our own rankings find. A rerun on our ranked heads is an ungated extra.
   Rejected: our rankings (a different claim); published-if-matched (a fork
   chosen after seeing data).
8. **Set knockout is a sibling module** (`src/lesion/knockout.py`), built
   from the existing primitives. `interventions.py`, `runner.py`,
   `reference.py` and `spec.py` stay untouched. `ioi.py` (a template subset)
   and `artifact.py` (a `set` block; `build_record(phase=...)`) change
   additively. Logged as forced generalisations under D-014 item 6.
9. **Induction ablation (I3) gets verdict `measured`.** Olsson et al.'s
   expectation is stated beside it as coming from other models, not as a
   published GPT-2 small claim. Their in-context learning score is deferred:
   it needs a natural-text dataset the battery does not have.

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
*Resolved 2026-09-19 — see below.*

The ablation method defines the task; the corruption scheme in patching
plausibly does the same. Should E2/E3 sweep corruption schemes the way they
sweep ablation methods, or is that scope creep? **Resolve during R1.**

*Addendum, 2026-09-19 (Wang extraction).* Evidence that the answer is "it is
part of the measurement, whatever E3 decides to sweep". Wang et al. chose
`p_ABC` as both the mean-ablation reference and the path-patching corruption
*because* `p_IOI` "would not remove enough information helpful for the task"
— duplication is constant across `p_IOI`, so a mean over it keeps the
signal a Duplicate Token head carries [wang-2022 §2.1]. Their Appendix A
then builds six counterfactual datasets each removing or inverting one
named signal, and the logit difference decomposes additively across them.
So a corruption scheme is a statement of *which information is removed*,
and two schemes that remove different information measure different
things. Proposed shape for the R1 resolution: E1 records, per battery item
and per corruption scheme, what the scheme removes (in the style of Wang's
random-name / position-flip / role-swap triple); E3 sweeps the scheme only
where a battery item has more than one natural corruption, and records the
one used everywhere else. Wiki: `methods/activation-patching.md`,
`methods/mean-ablation.md`.

*Addendum, 2026-09-19 (Miller extraction).* The corruption scheme is two
of Miller et al.'s six axes — the *value* (resample from which corrupt
distribution; mean over which reference) and the *direction*. Their Sports
Players case makes the cost concrete: because every corrupt prompt names a
different sport, resample ablation "adds signal" and the ablated model
scores 0% where chance is 33% [miller-2024 App. D.2]. So a corruption
scheme can inject a competing answer, not only delete the correct one, and
two schemes differ in what they inject. Supports the proposed shape above;
adds that E1 records, per scheme, what it *inserts* as well as what it
removes. Wiki: `methods/resample-ablation.md`.

#### Resolution — *2026-09-19*

**Adopted as proposed**, confirmed by the author after both addenda. The
corruption scheme is part of the measurement (Miller et al.'s value and
direction axes), not a nuisance parameter. Decided:

1. E1 records, per battery item and per corruption scheme, **what the
   scheme removes and what it inserts** — in the style of Wang et al.'s
   random-name / position-flip / role-swap triple and with the Sports
   Players "adds a competing answer" case as the warning.
2. E3 sweeps the corruption scheme **only where a battery item has more
   than one natural corruption**, and records the scheme used everywhere
   else next to the number.
3. IOI inherits `p_ABC` as its default scheme so E2 matches the published
   setup; the Appendix A transformations are available as named extras.

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

### O-007 — Are MLP layers a first-class component in the harness?
*Raised 2026-09-02. Direct-effect half resolved 2026-09-08. MLP half
**resolved 2026-09-20** — see the resolution below.*

D-003 chose heads over SAE features. In the roadmap that has become
"heads only": E3 ablates every head and nothing else. But the self-repair
literature E4 depends on locates a large share of compensation in MLPs —
Rushing & Nanda (arXiv 2402.15390) report sparse MLP neurons performing
"anti-erasure" alongside the LayerNorm-scaling share. If the harness only hooks
attention heads, E4's sub-question 3 ("which components step up?") is
structurally unanswerable, whatever the data says.

Making MLP layers (and ideally neurons) ablatable does not reopen D-003; the
unit of analysis stays coarse and published-number-checkable. It does add a row
type to the E3 heatmaps and a hook family to the E1 harness. **Resolve during
R1, before E1's harness design is fixed.** Also decide whether E3 records each
head's *direct effect* next to its total ablation effect — the gap is the
self-repair number, it is nearly free in TransformerLens, and it gives E4 its
baseline from E3's own run.

*Update 2026-09-08:* the direct-effect half is settled — **yes**, recorded per
head in the same E3 run. It turned out to be the same design question as O-011,
whose resolution treats total effect, pattern-preserving and direct effect as
three values of one path-restriction setting. The MLP half of O-007 is
unaffected and still resolves at R1.

*Addendum, 2026-09-19 (Wang extraction).* One measured datapoint for the MLP
half, on GPT-2 small, IOI, mean ablation on `p_ABC`: knocking out MLP0
alone *reverses the sign* of the logit difference; knocking out any other
MLP layer alone does little; knocking out every MLP except MLP0 gives −1.1
[wang-2022 App. J]. Wang et al. did not intervene on MLPs anywhere else and
list them as not understood. Two things follow for E1: MLPs matter
*collectively* on this task while looking unimportant *individually*, which
is exactly the pattern a per-component heatmap cannot show; and MLP0 is a
special case that any MLP-level sweep should expect to dominate. Neither
resolves O-007; both argue for the hook family being cheap to add now.

*Addendum, 2026-09-19 (Miller extraction).* MLPs are *granularity* (axis 1)
in Miller et al.'s six-tuple, and "heads and MLPs" is the most common
setting in the circuit literature they survey (ACDC, Greater-than, Sports
Players); Wang et al. are the exception, treating MLPs "as part of the
direct path between nodes" [miller-2024 §3.1.1, App. F]. Nothing in the
paper measures MLP ablations on their own. For O-007 the point is that
"heads only" is a *choice on a named axis*, and the harness should record
it as one whether or not E3 sweeps it. Wiki: `methods/ablation-methodology.md`.

*Status, 2026-09-19.* The author leans **yes** — MLP layers become
ablatable in the E1 harness — on the Wang evidence (MLPs matter
collectively on IOI, MLP0 dominates) and the Miller framing (granularity is
a named axis; "heads and MLPs" is the literature default). The final
decision is deferred until Meng et al. (ROME) is extracted, since causal
tracing localises factual recall to MLP layers and is the third R1 source
bearing on this. The direct-effect half was settled 2026-09-08; the MLP
half stays open pending that one read.

*Addendum, 2026-09-20 (ROME skim).* The third datapoint is in. Meng et
al.'s causal tracing on GPT-2 XL finds its "early site" in MLP outputs at
the last subject token (peak AIE 6.6 points, versus 1.6 for attention at
that token), and severing the later MLPs at that token removes the effect
of restoring the hidden states below them [meng-2022 §2.2, Fig. 3]. Two
qualifications that bear on *how* MLPs go into the harness, not on
whether: (a) the MLP effect appears only when **ten consecutive layers are
restored together** — single-layer MLP restorations were "generally
negligible" [meng-2022 App. B.2], which is Wang's "collectively, not
individually" again, under the opposite direction and on a different
task; (b) nothing is measured on GPT-2 small, and the peak layer moves
between model sizes [meng-2022 App. B.3]. Wiki: `methods/causal-tracing.md`.

**Proposed resolution, for the author's call:** MLP layers become
ablatable in E1 as a hook family alongside heads (12 rows next to 144);
E3's per-layer MLP row is recorded as the single-layer measurement it is,
with the Wang and Meng window findings noted in the E3 README so a blank
row is read as expected rather than as a null; whether E3 also sweeps
*windows* of MLP layers is deferred to E3's design with the factual-recall
item as the case that would need it. Neurons stay out (D-003 granularity).
The only alternative with a real argument is "heads only, MLPs at E4",
which leaves the factual-recall item without its own reference experiment
and forces E4 to retrofit a hook family into E3's artifacts.

#### Resolution — *2026-09-20*

**Adopted as proposed**, confirmed by the author after the ROME skim. The
evidence is three sources pointing the same way on two tasks and two
directions: Wang (IOI, mean ablation, MLPs matter collectively and MLP0
dominates), Miller ("heads and MLPs" is the literature's default
granularity), Meng (factual recall, restore direction, the early site is
an MLP result at the level of ten-layer windows). Decided:

1. **MLP layers are an E1 hook family alongside heads.** Twelve rows next
   to 144 on GPT-2 small; same substitution values (D-006) and the same
   path-restriction setting (O-011) as heads. Neurons stay out — D-003's
   granularity is unchanged.
2. **E3's per-layer MLP row is recorded as the single-layer measurement it
   is.** The E3 README states, before any number, that both Wang [wang-2022
   App. J] and Meng [meng-2022 App. B.2] found single-layer MLP effects
   small where multi-layer ones were large, so a blank MLP row is the
   expected reading, not a null result. MLP0 is flagged as the expected
   exception on IOI.
3. **Whether E3 also sweeps windows of MLP layers is deferred to E3's
   design**, with the factual-recall battery item as the case that would
   need it. Not decided now.
4. The direct-effect half (2026-09-08) stands unchanged.

Consequence for the roadmap: E1's harness sentence "over any component"
now means heads and MLP layers explicitly. Recorded in `docs/02-roadmap.md`
in this commit. O-007 is closed; nothing about it remains pinned to R1.

### O-008 — How much of E4 is reproduction rather than extension?
*Raised 2026-09-02.*

E4 sub-question 1 (measure self-repair per ablated head, decompose into the
LayerNorm-rescaling share and the residual) is, as written, the central result
of Rushing & Nanda 2024: resample ablation of individual heads on Pythia,
GPT-2 small/medium and LLaMA-7B, with LayerNorm scaling attributed around 30%
of direct effect on average and explicitly described by the authors as a
directional figure rather than a precise one. They also compare mean and zero
ablation and note zero ablation distorts residual norms.

That is fine for a reproduction-first project (D-001), but the roadmap text
reads as if the decomposition itself is the contribution. The plausibly open
pieces are sub-question 2 (how the mechanical/residual split moves across
ablation methods) and sub-question 4 (compensators of compensators). **Resolve
during R2**, after reading the paper properly: relabel sub-question 1 as the
E4 reproduction with a published number to check against, and state which
sub-questions are the extension. From the abstract alone, Conditional
Co-Ablation (arXiv 2607.01940, verified to exist, submitted 2026-07-02) is a
method for recovering the *identity* of backup components on the GPT-2 IOI
circuit, not a decomposition of self-repair — so on current evidence it does
not close E4, but O-001 still stands until it is read.

### O-009 — Does factual recall pass a clean-accuracy gate on GPT-2 small?
*Raised 2026-09-02.* *Resolved in design 2026-09-23 — see below; the measured outcome
lands at E1b execution.*

D-005 dropped arithmetic because GPT-2 small does not do it well enough for
lesion results to beat noise. Factual recall may have the same problem: ROME's
causal tracing was run on GPT-2 XL and GPT-J, and GPT-2 small answers only a
small fraction of ROME-style prompts correctly. A task the clean model gets
wrong has no clean/corrupted gap to lesion.

Two sub-decisions. First, whether the battery keeps factual recall with an
explicit filter (only facts the clean model answers correctly, filter recorded
in the battery artifact), or drops it. Second, more generally, whether every
battery item needs a stated clean-accuracy threshold before it enters E3 — a
cheap rule that would have caught arithmetic without a separate decision. A
control task the model does trivially, where every ablation should read near
zero, would give the heatmaps a noise floor for the same price. **Resolve
during E1**, when the generators exist and the number can be measured rather
than guessed.

*Addendum, 2026-09-08 (Olsson extraction).* A related and cheaper rule surfaced
while reading Olsson et al.: state, per battery item, **which direction damage
is expected to move the metric**. Their in-context learning score is a
difference of two losses, so ablating most non-induction heads *raises* it —
damage improves the number, for a comprehensible reason. A metric that can
improve under ablation is not disqualifying, but it has to be declared, or the
E3 heatmaps will contain sign flips that read as noise.

*Addendum, 2026-09-20 (ROME skim).* The filter O-009's first sub-decision
proposes is what Meng et al. did: keep a prompt only if the clean model's
greedy generation names the correct object before any other capitalised
word, use the text up to the object as the prompt, and record the survivor
count (1000 sampled; mean correct-object probability 27.0% on GPT-2 XL)
[meng-2022 App. B.1]. So "keep with an explicit filter" has a published
form to copy, and the number to measure at E1 is the survivor count on
GPT-2 small. Two things the source does not settle: the smallest model
traced is GPT-2 Medium, so whether small shows an early site at all is
open; and the paper's metric is the correct-object probability, so the
battery item's logit-difference version (rule 5) is a translation and
should be reported next to the probability version until the two are
shown to agree. Wiki: `methods/causal-tracing.md`.

#### Resolution — *2026-09-23*

Confirmed by the author during E1b design (D-013, D-014).

1. **Factual recall stays, filtered.** ROME's known-facts rule is copied and
   re-run on GPT-2 small; the survivor count is logged and gated at ≥ 300.
   Whether GPT-2 small clears it is measured at execution, not assumed. If
   it fails, subject–verb agreement enters as an unsourced fallback (D-013).
2. **Every item has a stated clean-accuracy threshold** (D-014 item 1).
3. **No control item.** The premise that a trivial task reads near zero
   under every ablation does not hold (a trivial task still depends on
   components, e.g. MLP0), and it would be one more unsourced item. The
   noise floor is statistical instead: per-cell standard error plus the
   spread across mean-reference seeds, measured on a fixed sample of
   components per item. Generic-versus-specific damage is read off the map
   across the three items.
4. **Expected direction** is declared per item (the Olsson addendum), and
   factual recall reports `P[o]` beside `ld` (the ROME addendum).

### O-010 — What does E6 actually visualize over training?
*Raised 2026-09-02, during the R0 reading of Olsson et al.*

Olsson et al. show induction heads forming as a phase change over training,
visible in a derived score (loss late in context minus loss early in context)
and in a per-head prefix-matching score tracked across checkpoints. The
question this raises for E6: what per-checkpoint quantity does this project
track, and is a dimensionality-reduction "clusters evolving over time" picture
the right way to show it? The framing that makes the question concrete is
**"what is a point?"** — a head, a neuron, or a whole checkpoint.

Candidate observables, closest to the lesion method first:

1. **The E3 lesion map, recomputed per checkpoint.** Each head becomes a
   trajectory in effect space (tasks × ablation methods). A cheap 1D
   companion: distance between consecutive maps against the loss curve — a
   jump there is a phase change in the *map*, not just in the loss. Needs
   nothing the E1 harness won't already have.
2. **Behavioural head scores without ablation.** Induction score and
   previous-token score on repeated random sequences; copying score from the
   OV circuit. This is Olsson's own figure and gives E6 a published result to
   reproduce first.
3. **Weights only.** The K-composition score between a previous-token head and
   a candidate induction head, from the Elhage et al. framework. Data-free,
   and it marks *circuit* formation rather than head formation.
4. **Gradients / loss-surface geometry.** Weakest fit: checkpoints give
   weights, not dynamics, and this is the developmental-interpretability
   programme, a different project. See `notes/02-loss-surface-programme.md`.

Caution to carry into the planning: with ~100–150 heads, UMAP/t-SNE will
manufacture clusters from hyperparameters. A 2D scatter of two *named* scores,
animated over checkpoints, shows the same thing and can't lie about it.
Dimensionality reduction only earns its place if the per-head vector is long
(candidate 1), and then rule 7 applies to any clean-looking cluster.

Depends on O-004 (checkpoint density in the formation window). Prior work to
read before planning: Tigges et al. 2024 (already on the R3 list) and the
developmental-interpretability line noted above. **Resolve if and when E6 is
planned** — this entry is a record, not a plan. Original wording of the idea in
`notes/01-visualizing-circuit-formation.md`.

### O-011 — Is attention-pattern freezing a third axis of the ablation sweep?
*Partially resolved 2026-09-08 — see the resolution below. R1 trigger
resolved 2026-09-19 — see the second resolution.*
*Raised 2026-09-08, during the R0 extraction of Olsson et al.*

D-006 commits E3 to sweeping *what value is substituted* — zero, mean, resample.
Olsson et al. use a second, independent axis: *what is allowed to propagate*.
Their **pattern-preserving ablation** runs the model once to record every
attention pattern, then re-runs it with the head's output zeroed and all
patterns forced to the recorded values, so the ablation reaches later heads'
value computations but not their attention patterns. Their **full ablation**
lets everything propagate. Every number in the paper's model analysis table is
pattern-preserving; full-ablation results are relegated to an appendix and the
two are never compared numerically
[`wiki/methods/pattern-preserving-ablation.md`].

Why this is not a detail:

- **E2 cannot reproduce the induction-head ablation result without it.** A
  number computed with unfrozen patterns is a different measurement, and by
  epistemic rule 3 that difference is a finding rather than something to smooth
  over.
- **The justification does not transfer to GPT-2 small.** With patterns frozen,
  a head's action is linear, so in an *attention-only* model a pattern-preserving
  ablation equals subtracting that head's terms from the logits. The authors
  state plainly that this breaks once MLPs are present, and name two ways head
  ablations can then mislead: shifting an MLP's activation statistics enough to
  break neurons without the head mattering, and an MLP mechanism that needs two
  heads but limps along on one.
- **It is nearly free in TransformerLens and impossible to retrofit** into
  results already computed — the same argument O-007 makes for MLP hooks and for
  recording direct effect alongside total effect.

The cost is real: crossing this axis with D-006 turns three E3 heatmaps into
six. The middle option is to support freezing in the harness, run it on the E2
reproduction and on a named subset of E3, and record the default explicitly
wherever it isn't swept.

**Resolve during R1, alongside O-007, before E1's harness design is fixed.**
Miller et al. is the right place to check whether the faithfulness literature
treats pattern freezing as an ablation-methodology choice in the sense D-006
means, or as something separate.

---

#### Resolution — *2026-09-08*

**The framing was wrong, and fixing it is most of the answer.** Zero, mean and
resample vary *what you substitute*. Freezing varies *which downstream paths the
perturbation is allowed to travel*. Those are different kinds of choice, and
there is a third point on the same line that O-007 already raises. They nest:

| Setting | What the ablation reaches |
|---|---|
| **Total effect** | Everything downstream (full ablation) |
| **Pattern-preserving** | Later components' value computations, but not their attention patterns |
| **Direct effect** | Only the head's own contribution to the logits |

So O-011 and the second half of O-007 are one dimension seen from opposite ends.
The harness gets **one path-restriction setting with three values**, not a
boolean flag bolted onto the substitution sweep. Deciding them together also
means E3 hands E4 its baseline from E3's own run, which was O-007's point.

Decided now:

1. **E1 builds it.** Two forward passes instead of one — cache the patterns,
   replay them while zeroing the head. Trivial on GPT-2 small, and impossible to
   retrofit into results already computed. Same argument as MLP hooks. Exact
   hook mechanics get verified at E0, not designed here.
2. **E3 records direct effect for every head in the same run**, alongside total
   effect. This settles that sub-part of O-007 in the affirmative; the rest of
   O-007 (MLPs as a first-class component) is untouched and still R1.
3. **E2 runs pattern-preserving**, because that is what Olsson et al. do. With
   the limit stated in the results doc: they publish no GPT-2 small ablation
   numbers, so E2 reproduces their *method*, not a number of theirs.
4. **E3 ships four maps, not six.** D-006's three stay the headline at total
   effect. Add the frozen-pattern variant for **one** substitution value —
   whichever R1 settles as the in-distribution default — and report the delta
   against its unfrozen twin. A large delta escalates to the full cross with a
   measured reason behind it; a small one is a one-paragraph negative result
   (logged per epistemic rule 8) and three clean maps.

**Reasoning for holding at four.** The cost that matters is not compute — GPT-2
small has 144 heads and the sweep is cheap either way. It is that six maps × N
battery items is a large number of pairs, some of which will disagree
strikingly by chance. Epistemic rule 7 then obliges an adversarial check on each
one, and rule 3 says the disagreement *is* the finding. Sizing the sweep is
about protecting the claims, not the GPU. Decision 4 buys the same information
with one comparison instead of fifteen.

**What is still open, and the trigger.** If R1 shows the faithfulness literature
treats path restriction as a first-class methodology choice on par with the
substitution value, it belongs in D-006 proper and E3 runs the full cross. That
is a decision to make with Miller et al. open. `auto-circuit` may also already
implement it, in which case the right shape is theirs rather than one invented
here. Until then, **wherever an axis is not swept, the setting used is recorded
explicitly next to the number** — a default that goes unstated becomes a
permanent choice nobody made.

One more thing to carry into E4 rather than decide now: the paper already
contains the self-repair caveat, in 2022, with both of its causes named — "to
the extent two heads do something similar and the layer norm before the logits
rescales things, the importance of individual heads may be masked"
[olsson-2022 §Argument 3]. That is useful provenance for the E4 framing and for
O-008's question about what in E4 is reproduction and what is extension.

*Addendum, 2026-09-19 (Wang extraction) — "direct effect" is ambiguous and
"freezing" is overloaded.* The resolution table defines *direct effect* as
"only the head's own contribution to the logits", and
`wiki/methods/path-expansion.md` restates it as keeping only the head's own
term. Wang et al.'s direct effect is their path patching with the receiver
set to the final residual state: every path from the head to the logits that
does not pass through another *head* — MLPs and LayerNorms are recomputed
and so mediate it [wang-2022 §3.1, App. B]. The two coincide in an
attention-only model and differ in GPT-2 small by exactly the MLP-mediated
terms. Separately, Wang et al.'s "freezing" pins other heads' *outputs*;
Olsson et al.'s pins attention *patterns*; so the path-restriction axis has
at least three distinct points (total · patterns frozen · other heads
frozen) before "direct effect" is defined. **Proposed for the E1 design
note, not decided here:** name the direct-effect setting by its source
(`direct-effect/wang`: other heads frozen, MLPs recompute; or
`direct-effect/term`: MLPs held as well), implement at least the Wang
version because E2's IOI reproduction needs it verbatim, and record the
choice next to every E3 direct-effect number. Wiki:
`methods/path-patching.md`, `methods/pattern-preserving-ablation.md`.

*Addendum, 2026-09-19 (Miller extraction) — the R1 trigger, answered in
two halves.* The trigger asked whether the faithfulness literature treats
path restriction as a first-class methodology choice on par with the
substitution value. Miller et al.'s six-tuple has **component type** —
node, edge, branch — which restricts which downstream destinations receive
the change, and they show it is consequential: evaluating the IOI circuit
at the edge level instead of the node level moves faithfulness from 87% to
a median "well over 100%" [miller-2024 §4.1]. That half of the trigger
fires: edge-vs-node belongs in D-006's frame alongside the value axis.
**Attention-pattern freezing is absent** from the taxonomy and from the
paper; the nearest axis (edge ablation) still lets a destination's pattern
respond to its other inputs. That half does not fire. Miller et al. also
name Wang's direct effect as "Edge Resample Ablation" with MLPs "part of
the direct path between nodes" [miller-2024 App. F], which is the
definition question in the previous addendum, restated in their terms.
`auto-circuit` implements edge patching but not pattern freezing
[miller-2024 App. A].

**Proposed resolution shape (author decides):**

1. Reframe E1's path-restriction setting in Miller's vocabulary: the
   harness supports **node** and **edge** ablation (edge = Wang's path
   patching = the direct-effect setting, with the MLP convention named).
   This replaces "three nesting values" with two literature-standard ones
   plus a convention flag.
2. Keep **pattern freezing** as this project's own, separately named
   intervention, inherited from Olsson et al. and required for E2's
   induction reproduction — not folded into D-006, not claimed to be
   standard, and reported with the O-011 delta as planned.
3. E3's "four maps" stand: three values at node level, plus one
   pattern-frozen twin. Whether an *edge-level* map is also worth a run is
   an E3 question with a measured reason behind it.

Wiki: `methods/ablation-methodology.md`, `methods/pattern-preserving-ablation.md`.

*Addendum, 2026-09-20 (ROME skim) — a third "direct effect".* Meng et
al. compute and discard a "direct effect" as "noisy and uninformative, in
line with results by Vig et al." [meng-2022 §2.1 fn. 3]. That is Pearl's
mediation-analysis direct effect: the part of the *corruption's* effect on
the output that does not pass through the restored state. It is neither
Wang's edge-to-logits path patching nor the resolution table's "only the
head's own contribution to the logits". Recorded so that fn. 3 is never
cited for or against E3's direct-effect maps; the E1 design note that
defines the project's term should say which of the three it is not.

#### Resolution of the R1 trigger — *2026-09-19*

**Adopted as proposed**, confirmed by the author. Decided:

1. E1's path-restriction setting is restated in Miller et al.'s
   vocabulary: the harness supports **node** ablation and **edge**
   ablation. Edge ablation to the logits is Wang et al.'s path patching
   and is the project's *direct effect*; the harness names the MLP
   convention (`wang`: MLPs recompute on the direct path; `term`: MLPs
   held) as a flag and defaults to `wang`, because E2 needs it verbatim.
   "Three nesting values" is superseded by this.
2. **Pattern freezing** stays as this project's own, separately named
   intervention, inherited from Olsson et al. and required for E2's
   induction reproduction. It is not folded into D-006, not described as
   literature-standard, and is reported with the O-011 delta as planned.
3. E3's **four maps stand**: three substitution values at node level, plus
   one pattern-frozen twin. An edge-level map is an E3 question to be
   raised with a measured reason.
4. The 2026-09-08 decisions (E1 builds it; E3 records direct effect per
   head; E2 runs frozen; record the default wherever an axis is not swept)
   are unchanged.

`docs/02-roadmap.md` E1 updated to match in the same session.

### O-012 — Which induction mechanism does GPT-2 small use?
*Raised 2026-09-14, during the R0 extraction of Elhage et al. 2021. Confirmed
as an open question by the author 2026-09-19. Resolves at E2.*

Two mechanisms produce an induction head, and they leave different fingerprints
in the weights:

1. **K-composition with a previous-token head** — the mechanism reverse
   engineered in Elhage et al.'s two-layer models and restated by Olsson et al.
   The induction head's *key* reads the subspace where a previous-token head
   wrote the preceding token's identity
   [`wiki/concepts/attention-head-composition.md`].
2. **Positional pointer arithmetic** — available only when positional
   embeddings are in the residual stream, which the paper's own models lack
   and GPT-2 has. An earlier head fetches the positional embedding of a prior
   copy of the current token; the induction head's *query*, via Q-composition,
   shifts it one position forward. Elhage et al. report "at least one case in
   GPT-2" with no model size, head index or figure; Olsson et al. repeat the
   claim without adding detail.

Why it is project-level rather than a page note: E2 reproduces the induction
circuit on GPT-2 small, and a weight-based check built for mechanism 1 (large
K-composition score with a previous-token head; same-matching `W`) will read
*negative* on a head that uses mechanism 2, without that head being any less
an induction head behaviourally. A failed reproduction under the wrong
mechanism hypothesis would be a false negative logged as a null result.

**Resolve at E2, by measurement, before any ablation:** compute Q- and
K-composition scores for every (earlier, later) head pair
[`wiki/methods/weight-statistics.md`], identify the heads that pass Olsson's
behavioural evaluators, and record which composition route each one shows.
Both routes may coexist. Whatever E2 finds, the mechanism assumed by each
subsequent weight-based claim gets stated next to the claim.

*Addendum, 2026-09-19 (Wang extraction).* Behavioural evidence for
mechanism 1 on one task. Path patching on IOI finds Previous Token heads
4.11 and 2.2 affecting logit difference through the Induction heads' (5.5,
6.9) *keys* at S1+1 — the K-composition route — and, testing the Q-route
directly, "did not find any significant effect" on the Induction heads'
queries at S2 [wang-2022 App. D]. Wang et al. also note that in IOI these
heads emit a *position* signal rather than copying a token, and that the
mechanism for that is not investigated [wang-2022 §3.3]. This does not
resolve O-012: it is one task, four heads, and path patching rather than
the weight-level check E2 plans; and the position-signal role means the
heads do something on IOI that neither mechanism description covers. It
does give E2 head indices to start from and a prior that the K-route will
show. Wiki: `concepts/induction-head.md`.

### O-013 — Does the harness ablate whole heads or (head, position) nodes?
*Proposed 2026-09-19, during the R1 extraction of Wang et al. Confirmed and
resolved by the author the same day — see below.*

Wang et al.'s unit of knockout is a **(head, token position) pair** — a
node in the computational graph — and their mean is computed per template
so that positions align. The 26-node IOI circuit is "1.1% of the total
number of (head, token position) pairs" [wang-2022 §1, §2.1]. Every
published number this project would check against at E2 — the 87%
faithfulness, the ≈ 5% drop after knocking out the Name Movers, the
minimality scores, the greedy incompleteness of 3.09 — is a per-position
figure.

The roadmap's E3 ablates "every head in GPT-2 small, one at a time", which
reads as whole heads at all positions. That is a different, coarser
intervention: it removes the head's contribution at positions where the
circuit never uses it, and on a battery item without a fixed template (the
induction item, say) there is no natural position to name.

Options, with what each costs:

1. **Whole heads everywhere.** Simplest harness; E3's heatmaps are
   per-head. E2 then cannot reproduce Wang et al.'s numbers as published,
   only a whole-head analogue, and the results doc has to say so.
2. **(head, position) nodes where the battery item has aligned positions,
   whole heads elsewhere.** E2 reproduces the published unit; E3 gains a
   position axis for templated items and loses comparability across items.
3. **Both, with the unit logged.** The harness takes a position mask per
   ablation; "all positions" is one value of it. Cheap in TransformerLens;
   the cost is in the results-doc discipline, not the code.

Lean toward 3 with E3 defaulting to whole heads and E2 using the published
unit — but this is a harness-design decision and belongs to the author.
Related: O-007 (the same question for MLP layers), O-011 (path
restriction is a third axis; position is a fourth).

*Addendum, 2026-09-19 (Miller extraction).* Token positions are axis 4 of
Miller et al.'s six-tuple, and their rule is direct: "if [a circuit] is
specified with token positions then it should be tested with
token-specific ablation" [miller-2024 §5, §6]. Measured on IOI: ablating
at every position instead of the circuit's "consistently results in lower
faithfulness scores" [miller-2024 §4.1]; on Docstring the drop was large
enough to suggest the circuit "is in fact performing significant
computation on token positions outside the circuit" [miller-2024 App.
D.1]. Two consequences for the options above: option 1 (whole heads
everywhere) cannot reproduce any published IOI faithfulness figure without
a stated mismatch; and a position-masked harness (option 3) is the
literature-standard shape, not an extra. Strengthens the lean toward 3.

#### Resolution — *2026-09-19*

**Option 3, confirmed by the author: both units, with the unit logged.**
The harness takes a **position mask** per ablation; "all positions" is one
value of it. E3 defaults to whole heads (all positions), which is what a
per-head heatmap means. E2 uses the published (head, position) unit with
template-matched means so Wang et al.'s numbers are reproduced as stated.
Every result artifact records the mask. Position is thereby axis 4 of the
six-tuple in the harness config, alongside substitution value and node/edge
component type (O-011).

---

### O-014 — Which tokenisation and template mix did Wang et al. actually use?
*Proposed 2026-09-20, from the E0 run. Not resolvable from the paper or its
released code; see D-011.*

The paper says 15 templates, ABBA and BABA orders, 100 names, 20 places, 20
objects, and reports 3.56 [wang-2022 §2, App. E]. The released code has 99
names, 8 places, 8 objects, defaults to no BOS, and its `mixed` mode with the
default template count silently uses 7 templates per order. E0 measured 3.65
(15 per order, no BOS), 3.49 (7 per order, no BOS) and 3.92 (15 per order,
BOS). The BOS variant is ruled out by the size of its miss; the other two
bracket the paper.

**Why it matters:** the per-template means span 2.5 to 5.0, so the template
mix moves the baseline by more than most single-head interventions in the
paper. Any E2 comparison of an absolute level against the paper inherits
this. **Resolution path:** an author-side answer (the released experiment
notebooks, or asking), or accept the bracket and compare only deltas. The
harness (E1) should carry `prepend_bos` and the template set as logged
parameters of every IOI artifact.

### O-015 — E3's reference n for IOI
*Raised 2026-09-23, from the E1b gate. Needs the author's decision; not
resolved here.*

D-014 item 5 admits a template into a mean-ablation run only with ≥ 30
reference prompts, anchored on E1a's IOI reference averaging ≈ 33 per
template. The E1b gate measured the per-template counts of one `p_ABC`
reference draw at ref n = 1,000, ref seed 0
(`uv run python -m src.lesion.e1b_gate --item all`,
`results/E1b/gate/ioi/p_ABC.json`, `reference_floor`): minimum 22, and five
of the 30 templates below 30 — ABBA/7 (22), ABBA/8 (28), ABBA/9 (28),
BABA/1 (28), BABA/3 (25). The E1a MLP mean-ablation artifacts use the same
draw and record the same counts. Induction at ref n = 1,000 has minimum 37
(none below 30).

**Why it matters:** E3's IOI heatmaps at ref n = 1,000 would include
templates that do not meet the project's own floor. The noise floor
(`results/E1b/noise/ioi/floor.json`) was measured at ref n = 1,000.
**Resolution path:** the author's call on the reference n (or on how the
floor is applied) before E3 runs IOI; E1b does not choose.

#### Resolution — *2026-09-24*

Options proposed by Claude; the author chose **ref n = 2,000 for both
passing items** (IOI and induction), so mean-ablation numbers use the same
reference size across the E3 map. The floor of 30 is unchanged; only the
sample size needed to meet it was chosen.

Basis: the minimum per-template count of the `p_ABC` reference draw under
the five reference seeds the noise floor uses (0–4), from the prompt
generator's template stream (a scratch count, not an artifact; the rerun
gate records the seed-0 count). At n = 1,000 every seed misses the floor
(minimum 22–25; 5–7 templates under 30), so seed 0 was not an unlucky draw.
The smallest n meeting the floor was 1,102–1,350 depending on seed. At
1,500 the minimum is 33 (seed 3), which is too thin a margin; at 2,000 it is
48–54. Rejected: keeping 1,000 and dropping the templates under the floor
(this moves IOI away from Wang's template mix, and which templates are
dropped depends on the seed); a stratified draw (would change the generator
or `reference.py`, which nothing forces).

Consequences: `REF_N` is 2,000 in `e1b_gate.py` and `e1b_noise.py`; the gate
and both noise floors are rerun at 2,000. The 1,000 noise floors stay in
history at `74a659a`. E1a's MLP numbers keep their reference n of 1,000, as
logged in their artifacts.

## Null and negative results

*Anything that fails to reproduce, fails to replicate, or comes out null goes
here at full strength with a link to the results artifact. Deleting these
destroys the most useful information the project produces.*

| Date | Phase | What was expected | What happened | Artifact |
|---|---|---|---|---|
| 2026-09-20 | E0 | Wang et al.'s clean mean logit difference on `p_IOI`, 3.56 over 100,000 samples, reproduced exactly from the released templates and word lists. | 3.648 ± 0.005 (no BOS, 15 templates per order), 3.485 (no BOS, 7 per order), 3.922 ± 0.006 (BOS). Not matched at 2 dp; bracketed by the two no-BOS readings. Released word lists differ from the paper's text; paper-era lists unrecoverable. IO-over-S 99.4% vs 99.3% and IO probability 52.7% vs 49% are close. See D-011, O-014. | `results/E0/e0_smoke_seed0_n100000.json` |
| 2026-09-20 | E1a | Wang et al. App. J: mean-ablating MLP0 alone on `p_ABC` reverses the sign of the mean logit difference; no other single MLP layer does much. | Under node mean ablation (reference `p_ABC`, n=1,000, template-matched), n=2,000, seed 0, no BOS: MLP0 -0.401 (sign reversed); largest other layer L5 +0.406. Zero: MLP0 -1.405 (sign reversed); four other layers past 0.5 (L4 +0.730, L10 +0.711, L5 +0.652, L6 +0.512). Resample: MLP0 -0.816 (sign reversed); one other layer past 0.5 (L5 +0.531). Bracket, not match: reference and sample sizes are ours. | `results/E1a/README.md` |
| 2026-09-23 | E1b | Factual recall (`subject_swap`): pre-registered gate holds on all three thresholds — pairwise accuracy mean 1[ld_clean > 0] >= 0.90, gap mean ld_clean - mean ld_corrupt >= 1.0 logit, and (factual recall only) >= 300 admitted survivors. | n=64, seed 0, no BOS. Pairwise accuracy 1.000 >= 0.90, pass. Gap +4.104 ± 0.374 >= 1.0, pass. Survivors 64 < 300, fail. Verdict: FAIL, on the survivors condition alone. 64 is the full admitted pool from the CounterFact survivor filter, not a subsample. | `results/E1b/gate/factual/subject_swap.json` |
