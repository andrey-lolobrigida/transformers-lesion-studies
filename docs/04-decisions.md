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

### O-007 — Are MLP layers a first-class component in the harness?
*Raised 2026-09-02.*

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
*Raised 2026-09-02.*

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
*Partially resolved 2026-09-08 — see the resolution below. The R1 trigger keeps
it open.*
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

---

## Null and negative results

*Nothing yet. Anything that fails to reproduce, fails to replicate, or comes
out null goes here at full strength with a link to the results artifact.
Deleting these destroys the most useful information the project produces.*

| Date | Phase | What was expected | What happened | Artifact |
|---|---|---|---|---|
| — | — | — | — | — |
