# E1b — Task battery: gate, reference floor, noise floor

*Run 2026-09-23 on branch `phase-E1b-battery`, GPT-2 small at HF revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`. Survivor file written at repo commit `f1afd56`
(committed in `ad9dcd3`); gate artifacts and noise floors rerun on 2026-09-24 at `20fb4a9`, reference n 2,000
(O-015); the 1,000 versions are at `ad9dcd3` (gate) and `74a659a` (noise) (each
artifact's own `environment.repo_commit`). Subject–verb agreement (the D-013 fallback, section 10)
was run on 2026-09-24: gate at `718ec4b` (committed in `17cb218`), noise floor at `17cb218`
(committed in `e460d90`). Interpretation
of the artifacts in this directory and of `batteries/factual/survivors.json`. Decisions:
D-013, D-014, the O-009 and O-015 resolutions.*

## 1. What this is

E1b builds the battery that E2 and E3 measure on: four items, three of which passed their
gate (IOI, induction, subject–verb agreement) and one of which failed (factual recall), each with a clean/corrupt generator, a metric (`ld = logit[c] − logit[s]` at `END`),
a declared expected direction (`positive` for every item: damage is expected to lower `ld`)
and a corruption scheme whose `removes`/`inserts` are recorded in every artifact. The rules
it is measured against — the pre-registered clean-accuracy gate, the per-template reference
floor of 30, the statistical noise floor instead of a control item, filtering only for
factual recall — are recorded in D-014 and the O-009 resolution; the item order and the
agreement fallback in D-013. Factual recall failed its gate, so the fourth item, subject–verb
agreement, was built as that fallback: ours and unsourced (section 10). Everything below is measured on the clean model with no
intervention, except the noise floor (section 7), which is a mean-ablation sample.

## 2. Commands

Every artifact records its command, seed, n, BOS setting, model revision, library versions
and determinism flags. All runs use model revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`.

| What | Command | Seed / n |
|---|---|---|
| Factual survivor file | `uv run python -m src.lesion.counterfact` | greedy decoding, no seed; all 21,919 CounterFact records; no BOS; 10 generated tokens |
| Gate, all nine (item, scheme) pairs | `uv run python -m src.lesion.e1b_gate --item all` | seed 0; n = 2,000 for IOI and induction, n = 64 (every admitted survivor) for factual; reference-floor count at ref n = 2,000 (factual: 64), ref seed 0 |
| Identity against E0 | `uv run python -m src.lesion.ablate --battery ioi --component L0H0 --value zero --type node --positions all --direction ablate-clean --no-freeze --n 100000 --seed 0 --prepend-bos false --batch-size 512 --out-dir results/E1b/identity` | seed 0, n = 100,000, no BOS |
| Noise floor, IOI | `uv run python -m src.lesion.e1b_noise --item ioi` | seed 0, n = 2,000, ref n = 2,000, ref seeds 0–4, no BOS |
| Noise floor, induction | `uv run python -m src.lesion.e1b_noise --item induction` | seed 0, n = 2,000, ref n = 2,000, ref seeds 0–4, BOS prepended |
| Gate, agreement (`number_flip`, `number_flip_all`) | `uv run python -m src.lesion.e1b_gate --item agreement` | seed 0, n = 2,000, BOS prepended; reference-floor count at ref n = 2,000, ref seed 0 |
| Noise floor, agreement | `uv run python -m src.lesion.e1b_noise --item agreement` | seed 0, n = 2,000, ref n = 2,000, ref seeds 0–4, BOS prepended |

The `--item all` row produced the IOI, induction and factual artifacts before agreement
existed; agreement was run on its own, and the other items' artifacts were not regenerated.

BOS defaults are per item (D-014 / E1b spec; D-013 addendum item 6): no BOS for IOI (as in
E0 and E1a) and factual recall, BOS prepended for induction and agreement.

Every gate artifact carries a top-level `pre_registered` field: the gate CLI writes a
verdict only when the run is at the pre-registered seed 0 and n (2,000; all admitted
survivors for factual), and all four gated artifacts here have `pre_registered: true`.

**Identity check.** Under no intervention (the clean pass of the identity run), on `p_IOI`,
seed 0, n = 100,000, no BOS, batch size 512, the mean `ld` is 3.6481308937072754
(± 0.005), bitwise equal to `results/E0/e0_smoke_seed0_n100000.json` on mean, std, sem,
IO-over-S fraction, mean IO probability and all 30 per-template means
(`tests/test_e1b_validation.py::test_identity_against_e0_after_the_protocol_change`). So
the E1b protocol changes did not move the default IOI stream. The artifact records
`"phase": "E1a"` because `artifact.build_record` hard-codes it (plan choice 16, left for E2).

## 3. Gate

Pre-registered thresholds (D-014 item 1, fixed before any generator ran; none is a
published value), applied to each item's **default** scheme only:

- pairwise accuracy, the mean of `1[logit[c] > logit[s]]` on the clean prompts, ≥ 0.90;
- gap, mean clean `ld` − mean corrupt `ld`, ≥ 1.0 logit;
- factual recall only: ≥ 300 survivors in admitted templates.

Named extras are measured and reported, not gated (`extra` in the table).

| item | scheme | verdict | n | pairwise acc | clean ld ± sem | corrupt ld | gap ± sem | fraction removed | top-1 | P[c] clean / corrupt | sd of clean ld | min per-template ref count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ioi | p_ABC | PASS | 2000 | 0.990 | +3.651 ± 0.036 | +0.062 | +3.590 ± 0.053 | 0.98 | 0.919 | 0.524 / 0.001 | 1.60 | 52 (0 below 30) |
| ioi | rand_names | extra | 2000 | 0.990 | +3.651 ± 0.036 | +0.039 | +3.613 ± 0.054 | 0.99 | 0.919 | 0.524 / 0.000 | 1.60 | 52 (0 below 30) |
| ioi | flip | extra | 2000 | 0.990 | +3.651 ± 0.036 | +3.632 | +0.019 ± 0.038 | 0.01 | 0.919 | 0.524 / 0.521 | 1.60 | 52 (0 below 30) |
| ioi | flip_rand | extra | 2000 | 0.990 | +3.651 ± 0.036 | +0.067 | +3.585 ± 0.056 | 0.98 | 0.919 | 0.524 / 0.000 | 1.60 | 52 (0 below 30) |
| ioi | repl_flip | extra | 2000 | 0.990 | +3.651 ± 0.036 | -3.642 | +7.293 ± 0.057 | 2.00 | 0.919 | 0.524 / 0.025 | 1.60 | 52 (0 below 30) |
| ioi | repl | extra | 2000 | 0.990 | +3.651 ± 0.036 | -3.597 | +7.248 ± 0.053 | 1.99 | 0.919 | 0.524 / 0.025 | 1.60 | 52 (0 below 30) |
| induction | fresh_prefix | PASS | 2000 | 0.999 | +17.005 ± 0.139 | -0.007 | +17.012 ± 0.138 | 1.00 | 0.974 | 0.768 / 0.000 | 6.22 | 71 (0 below 30) |
| factual | subject_swap | FAIL | 64 | 1.000 | +4.291 ± 0.312 | +0.187 | +4.104 ± 0.374 | 0.96 | 1.000 | 0.208 / 0.009 | 2.50 | 31 (0 below 30) |
| factual | subject_swap_sym | extra | 64 | 1.000 | +4.808 ± 0.293 | -2.676 | +7.484 ± 0.542 | 1.56 | 1.000 | 0.208 / 0.009 | 2.35 | 31 (0 below 30) |
| agreement | number_flip | PASS | 2000 | 0.983 | +2.611 ± 0.027 | -2.558 | +5.169 ± 0.041 | 1.98 | 0.059 | 0.033 / 0.002 | 1.22 | 229 (0 below 30) |
| agreement | number_flip_all | extra | 2000 | 0.983 | +2.611 ± 0.027 | -2.618 | +5.229 ± 0.045 | 2.00 | 0.059 | 0.033 / 0.002 | 1.22 | 229 (0 below 30) |

Columns: fraction removed is `(mean clean ld − mean corrupt ld) / mean clean ld`; top-1 is
the rate at which `c` is the argmax over the full vocabulary on the clean prompt; the last
column is the smallest per-template count in a reference draw at ref n = 2,000 (factual:
64), ref seed 0, with the number of templates under the floor of 30.

Per default scheme, per condition:

- **IOI:** on `p_ABC`, n=2000, seed 0, no BOS, the clean pairwise accuracy is 0.990 against
  0.90 and the gap is +3.590 ± 0.053 logits against 1.0. PASS.
- **Induction:** on `fresh_prefix`, n=2000, seed 0, BOS prepended, the clean pairwise
  accuracy is 0.999 against 0.90 and the gap is +17.012 ± 0.138 logits against 1.0. PASS.
- **Factual recall:** on `subject_swap`, n=64, seed 0, no BOS, the clean pairwise accuracy
  is 1.000 against 0.90 and the gap is +4.104 ± 0.374 logits against 1.0; the admitted
  survivor count is 64 against 300. FAIL, on the survivor condition alone.
- **Agreement** (D-013 fallback, unsourced; section 10): on `number_flip`, n=2000, seed 0,
  BOS prepended, the clean pairwise accuracy is 0.983 against 0.90 and the gap is
  +5.169 ± 0.041 logits against 1.0. PASS.

## 4. Factual recall

**Survivor funnel** (`batteries/factual/survivors.json`, `counts`; command in section 2):

| Field | Count | What it counts |
|---|---|---|
| `records` | 21919 | CounterFact records read (main rewrite prompt only) |
| `multi_token_target` | 0 | dropped: `" " + target_true` or `" " + target_new` is not a single token |
| `segment_misaligned` | 35 | dropped: segmentation filter (ours, below) |
| `pool` | 21884 | records passing both filters above |
| `not_known` | 19851 | dropped: ROME's known-facts filter, re-run on GPT-2 small, greedy, 10 tokens |
| `no_partner` | 68 | dropped: passed the known-facts filter but has no eligible swap partner (ours, below) |
| `known_with_partner` | 1965 | survivors before template admission |
| `templates` | 672 | distinct template keys among them (template string, subject token length, generated suffix ids) |
| `admitted_templates` | 2 | templates with ≥ 30 survivors |
| `admitted` | 64 | survivors in admitted templates: the gated count and the item's whole n |

Two of these filters are this project's additions, not ROME's:

- **Segmentation filter** (`segment_misaligned`): a prompt is kept only if tokenising its
  prefix, subject and rest separately gives exactly the whole-prompt tokenisation, so the
  subject can be swapped by token id without re-encoding.
- **Partner requirement** (`no_partner`): a survivor needs at least one eligible swap
  partner — another record with the same prompt template and subject token length whose
  true object is neither `o` nor this record's `target_new`; partners are drawn from `pool`,
  so they pass the single-token filter on both targets and the segmentation filter, but
  need not pass the known-facts filter.

The two admitted templates are `"The mother tongue of {} is|s4|g"` (31 survivors) and
`"{} is produced by|s4|g"` (33). How the 1,965 pre-admission survivors spread over the
672 templates, read from the file: the largest non-admitted templates hold 27
(`"The native language of {} is|s4|g"`), 26 (`"{}, developed by|s4|g"`), 25
(`"{} speaks the language|s5|g286.262"`) and 24 (`"The mother tongue of {} is|s3|g"`);
10 templates hold 20 or more survivors (248 in total), and 358 templates hold exactly one.

**Readings.** On `subject_swap`, n=64 (every admitted survivor), seed 0, no BOS: clean `ld`
+4.291 ± 0.312 (sd 2.50), corrupt `ld` +0.187, gap +4.104 ± 0.374, fraction removed 0.96.
Beside `ld`, the ROME-style probability reading (O-009 addendum): mean `P[o]` is 0.208 on
the clean prompts and 0.009 on the corrupt ones. The two readings are reported together
because ROME's metric is the probability and this item's is a translation into `ld`; E1b
does not test whether they agree per component.

Pairwise accuracy is close to automatic here: survivors already passed a generation filter
that required GPT-2 to produce `o`, so a high reading is not evidence of the item's quality;
the gate rests on the survivor count and the gap. The top-1 rate of 1.000 is likewise
expected by construction, since each prompt ends where greedy generation produced `o`.

**Verdict.** The gate fails on the survivor condition: 64 admitted survivors against a
pre-registered 300. Pairwise accuracy (1.000) and gap (+4.104 ± 0.374) clear their
thresholds. **D-013's fallback is triggered**, with survivors as the failing condition; the
agreement addendum was decided on 2026-09-24 (D-013), and the item was built and gated the
same day (section 10). The failure is logged in the null-results table
of `docs/04-decisions.md`.

The extra `subject_swap_sym` uses the same prompts and partners with `s` set to the
partner's own object `o′`. Because `s` differs, its clean `ld` differs too (+4.808 ± 0.293
against +4.291); its corrupt `ld` is -2.676, gap +7.484 ± 0.542, fraction removed 1.56,
and the corrupt pairwise accuracy is 0.172. Ungated. The spec runs named extras only on items that
pass; the gate CLI measured this extra on factual recall anyway, and it is reported because
it was measured.

## 5. IOI App. A extras

Five of Wang et al.'s App. A corruptions of `p_IOI` [wang-2022 App. A], as built in E1b.
All on `p_IOI`, n=2000, seed 0, no BOS; `c` and `s` stay the clean IO and S tokens, and the
clean `ld` is +3.651 ± 0.036 throughout. Ungated. Position and token signal are the spec's
table; the readings are the gate CLI's clean-model forward passes on the corrupt prompts.

| Scheme | Position signal | Token signal | corrupt ld | gap ± sem | fraction removed |
|---|---|---|---|---|---|
| `rand_names` | original | uncorrelated | +0.039 | +3.613 ± 0.054 | 0.99 |
| `flip` | inverted | original | +3.632 | +0.019 ± 0.038 | 0.01 |
| `flip_rand` | inverted | uncorrelated | +0.067 | +3.585 ± 0.056 | 0.98 |
| `repl_flip` | original | inverted | -3.642 | +7.293 ± 0.057 | 2.00 |
| `repl` | inverted | inverted | -3.597 | +7.248 ± 0.053 | 1.99 |

What each scheme changes, and what was measured:

- **`rand_names`** replaces IO and S with two fresh names, consistently at every occurrence,
  so neither `c` nor `s` is in the corrupt prompt; the repeated name keeps the S1 and S2
  positions. It removed 0.99 of the clean `ld` (corrupt `ld` +0.039).
- **`flip`** exchanges IO and S1. The corrupt prompt still contains `s` twice and `c` once,
  so its own non-repeated name is still `c`; only positions change. It removed 0.01 of the
  clean `ld`: the gap is +0.019 ± 0.038, within one standard error of zero, and the corrupt
  `P[c]` is 0.521 against 0.524 clean.
- **`flip_rand`** does both of the above, so neither `c` nor `s` is in the prompt and the
  repeated name sits at the IO and S2 positions. It removed 0.98 (corrupt `ld` +0.067).
- **`repl_flip`** replaces S2 with IO and then exchanges IO and S1, so `c` is now the
  repeated name at the S1 and S2 positions and `s` occurs once; the corrupt prompt's own
  non-repeated name is `s`. It removed 2.00 of the clean `ld`: the corrupt `ld` is -3.642,
  about the clean value with the sign reversed.
- **`repl`** replaces S2 with IO, so `c` occurs twice (IO and S2 positions) and `s` once,
  at S1; again the corrupt prompt's own non-repeated name is `s`. It removed 1.99 (corrupt
  `ld` -3.597).

Across the five rows the fraction removed sorts by the token-signal column (original ≈ 0,
uncorrelated ≈ 1, inverted ≈ 2); rows that share a token signal and differ in position
signal differ by 0.008 (`rand_names` vs `flip_rand`) and 0.012 (`repl_flip` vs `repl`). This is a
description of the clean model's output on these prompts, not a decomposition: Wang et
al.'s `2.31 S_pos + 0.99 S_tok` fit is obtained by patching the S-Inhibition heads, which
E1b does not do (E2), and no reproduction of it is claimed.

## 6. Reference floor

A template enters a mean-ablation run only with ≥ 30 reference prompts (D-014 item 5);
the gate reports it, the harness does not enforce it. Counts are for one reference draw at
ref seed 0. The reference n is **2,000 for IOI and induction** (O-015 resolution,
2026-09-24): at 1,000, IOI had five templates under 30 at ref seed 0 (minimum 22:
ABBA/7 22, ABBA/8 28, ABBA/9 28, BABA/1 28, BABA/3 25), and a count over ref seeds 0–4
put 5–7 templates under the floor at every seed. The 1,000 gate counts are in history at
`ad9dcd3`.

- **IOI** (`p_ABC`, ref n = 2,000, 30 templates): minimum 52, none below 30. The E1a
  MLP mean-ablation artifacts (`results/E1a/mlp/mean/`) keep their reference of n = 1,000
  and its per-template counts, as logged there.
- **Induction** (`fresh_prefix`, ref n = 2,000, 22 templates `i1`…`i22`): minimum 71, none
  below 30.
- **Factual recall** (`subject_swap`, ref n = 64, every admitted survivor, 2 templates):
  minimum 31, none below 30. Moot while the item's gate has failed.
- **Agreement** (`number_flip`, ref n = 2,000, 8 templates `{prep}/{congruency}`): minimum
  229 (`behind/incongruent`), none below 30.

## 7. Noise floor

Per passing item, default scheme, seed 0, n = 2,000: node mean ablation at all positions,
ablate-clean, reference n = 2,000 drawn from the default corrupt scheme and matched by
template, under reference seeds 0–4, for the 12 MLP layers and head 0 of each layer (24
components). Per component the floor is the larger of the standard deviation of
`effect_mean` across the five reference seeds and the per-prompt `sem` of the seed-0 run.

- **IOI** (`p_ABC`, no BOS): largest floor 0.0404, on L0.mlp, where the sem dominates
  (sem 0.0404 against spread 0.0240). The spread dominates in 2 of the 24 components
  (L4H0 and L7H0, both about 0.001), the sem in the other 22.
- **Induction** (`fresh_prefix`, BOS prepended): largest floor 0.1422, on L0.mlp, where the
  sem dominates (sem 0.1422 against spread 0.0728). The sem dominates in all 24 components.

Against the reference n = 1,000 floors (`74a659a`): on IOI the largest reference-seed
spread fell from 0.0459 to 0.0240 and the spread now dominates in 2 components rather than
5; the median per-component spread is 0.77 of its 1,000 value (range 0.29–1.60). On
induction the median is 0.91 (range 0.45–2.08) and the largest floor barely moves, since
the sem, which does not depend on the reference n, dominates there. Five seeds give a
rough estimate of each spread, so single-component ratios are noisy.
- **Factual recall:** no floor was measured, because its gate failed; `e1b_noise` refuses an
  item whose gate did not pass.
- **Agreement** (`number_flip`, BOS prepended): largest floor 0.2977, on L0.mlp, where the
  reference-seed spread dominates (spread 0.2977 against sem 0.0608). Under node mean
  ablation of L0.mlp on `number_flip` (n = 2,000, seed 0, ref n = 2,000), `effect_mean` is
  +1.494, +0.914, +0.856, +0.982 and +1.411 under ref seeds 0–4. The sem dominates in the
  other 23 components; the next-largest floor is 0.0246 (L8.mlp, sem). On IOI and induction
  L0.mlp also has the largest floor, but there the sem dominates it.

The rule for E3: **a heatmap cell under this item has to clear its component's floor, where
one was measured (the 24 components here); for other components E3 has to extend the
sample (spec, Risks).** The floor is measured under mean ablation at one reference size; it
is not measured for zero or resample ablation.

## 8. Obligation for later results docs

Per D-014 item 2, every later mean- or resample-ablation number cites, beside it, the
reference size and the fraction of the clean `ld` removed by the scheme its reference is
drawn from, taken from the table in section 3. For the three items that passed: `p_ABC`
removes 0.98 (IOI), `fresh_prefix` removes 1.00 (induction), `number_flip` removes 1.98
(agreement), each measured at n = 2,000, seed 0.

The agreement value is near 2 by design and measured at 1.98: `c` and `s` stay the clean
labels, so the corrupt prompt (subject in the other number) is built to favour `s` if the
model agrees, and on the clean model it does (mean corrupt `ld` -2.558 against clean
+2.611). Under resample ablation the source is that paired corrupt prompt, whose `ld` points
the other way, and 1.98 describes it. Under mean ablation the reference is the
template-matched mean over corrupt prompts (section 7), and subject number is not in the
template key, so that reference mixes both subject numbers (section 10); 1.98 is cited
beside a mean-ablation number per D-014 item 2, but it does not describe that reference's
direction.

## 9. What this does not show

- The gate is a clean-model sanity floor, not evidence of a circuit. Passing says the clean
  model separates `c` from `s` on these prompts and the corruption removes most of that
  separation (IOI, induction) or reverses it (agreement); it says nothing about which components do it.
- Nothing here is a necessity or sufficiency claim. The noise-floor runs are mean
  ablations, but they are used only to size noise; no component's effect is interpreted.
- The noise floor is a sample of 24 components under 5 reference seeds, not the floor for
  every cell E3 will produce.
- The IOI extras describe output on corrupt prompts; they do not reproduce Wang et al.'s
  App. A fit or show how GPT-2 small uses position or token information.
- The factual-recall readings rest on n = 64 prompts in two templates; they are reported
  because they were measured, and the item's gate has failed.
- The agreement item is ours and unsourced (D-013): no published number is checked against
  it, and its pass is not a reproduction of anything.
- The agreement breakdown (section 10) is ungated. Its per-condition differences are
  readings on one sample with no standard errors recorded, not tests, and they say nothing
  about which components are involved.
- The agreement prompts are one construction, `The {N1} {prep} the {N2}`, with 46 nouns,
  4 prepositions and 2 verb pairs, so a reading is about this construction, not about
  subject–verb agreement in general.

## 10. Subject–verb agreement (D-013 fallback; unsourced)

**Why it exists.** Factual recall failed its gate on the survivor condition (sections 3–4).
D-013 pre-registered agreement as the fallback for that case, because without a third item
the battery is IOI plus induction, which overlap through heads 5.5 and 6.9
[wang-2022 §3.3]. The item was built under the agreement addendum to D-013 (2026-09-24),
with the D-014 gate unchanged and its thresholds fixed before the generator ran.

**Labelling.** This item is ours and unsourced. It departs from reproduction-first: every
design choice below was made in this project, and no published number is checked against
it. Agreement has a literature, including work on GPT-2, but none of it is on the reading
list [unverified: Linzen, Dupoux & Goldberg 2016; Finlayson et al. 2021] (D-013, wording
correction).

**Design** (`src/lesion/agreement.py`; D-013 addendum items 1–6). Prompts are
`The {N1} {prep} the {N2}`, six tokens with BOS prepended, read at `N2` (`END`), where the
next token is the verb. `N1` and `N2` come from 50 candidate animate common nouns with
regular `-s` plurals, of which 46 are kept because singular and plural are each one token
(`owl`, `eagle`, `baker` and `painter` are dropped); `N2` is a different noun from `N1`.
`prep` is one of `near`, `behind`, `beside`, `with`. The attractor `N2` shares `N1`'s number
(congruent) or not (incongruent), 50/50. The verb pair, `is`/`are` or `has`/`have`, is drawn
per prompt and is not in the prompt: it picks the two logits `ld` reads, `c` the form that
agrees with `N1` and `s` the other form. The template key is `{prep}/{congruency}` (8
templates); subject number is not in it, so each template's mean-ablation reference mixes
both numbers: number-balanced in expectation (independent 50/50 draws), not exactly per
template. Default corruption `number_flip` replaces `N1` with its other-number form,
which turns congruent prompts into incongruent ones and back; the extra `number_flip_all`
flips both `N1` and `N2`, which keeps congruency. Under `number_flip` the corrupt side
carries the clean prompt's template key, so the mean reference for `{prep}/congruent` is
built from corrupt prompts that are incongruent on the surface, and the reverse; under
`number_flip_all` the key and the surface congruency agree. No prompt filter. The build choices the
addendum left open (the noun list, how draws are made, labels, the breakdown keys) are
pending the author's ruling at review and are not in the decision log.

**Gate.** Under no intervention, on `number_flip`, n = 2,000, seed 0, BOS prepended
(`uv run python -m src.lesion.e1b_gate --item agreement`, repo commit `718ec4b`): the clean
pairwise accuracy is 0.983 against 0.90 (pass) and the gap is +5.169 ± 0.041 logits against
1.0 (pass). **PASS.** Clean `ld` +2.611 ± 0.027 (sd 1.22), corrupt `ld` -2.558 ± 0.027,
fraction removed 1.98; on the corrupt prompts `logit[c] > logit[s]` in 0.021 of cases. The
failure branch of D-013 item 7 is not triggered.

**What pairwise accuracy measures here.** It compares only `c` with `s`. On the clean prompts
`c` is the argmax over the full vocabulary in 0.059 of cases, and the mean `P[c]` is 0.033
(0.002 on the corrupt prompts). So a pairwise accuracy of 0.983 says that the agreeing form
outscores the other form of the same verb, not that the model predicts that verb next; after
these prompts `c` is rarely the top next token.

**Breakdown** (ungated; n = 2,000, seed 0, BOS prepended; from the artifacts' `breakdown`
block; no per-condition standard errors are recorded). Clean `ld` and pairwise accuracy are
the same under both schemes, since the clean prompts are the same.

`number_flip` (gated scheme):

| key | value | n | pairwise acc | clean ld | corrupt ld | gap |
|---|---|---|---|---|---|---|
| congruency | congruent | 1024 | 1.000 | +3.181 | -2.008 | +5.189 |
| congruency | incongruent | 976 | 0.964 | +2.013 | -3.135 | +5.148 |
| verb | is/are | 1019 | 0.982 | +2.740 | -2.663 | +5.403 |
| verb | has/have | 981 | 0.983 | +2.477 | -2.449 | +4.925 |
| subject number | singular | 1038 | 0.997 | +2.885 | -2.308 | +5.193 |
| subject number | plural | 962 | 0.967 | +2.315 | -2.828 | +5.143 |

`number_flip_all` (extra):

| key | value | n | pairwise acc | clean ld | corrupt ld | gap |
|---|---|---|---|---|---|---|
| congruency | congruent | 1024 | 1.000 | +3.181 | -3.189 | +6.370 |
| congruency | incongruent | 976 | 0.964 | +2.013 | -2.019 | +4.032 |
| verb | is/are | 1019 | 0.982 | +2.740 | -2.717 | +5.457 |
| verb | has/have | 981 | 0.983 | +2.477 | -2.515 | +4.992 |
| subject number | singular | 1038 | 0.997 | +2.885 | -2.376 | +5.261 |
| subject number | plural | 962 | 0.967 | +2.315 | -2.879 | +5.194 |

Readings, not tests: on the clean prompts, pairwise accuracy is 1.000 on congruent and 0.964
on incongruent prompts (mean clean `ld` +3.181 against +2.013), and 0.997 with a singular
subject against 0.967 with a plural one (+2.885 against +2.315). The two verb pairs differ by
under 0.001 in pairwise accuracy (0.982 is/are, 0.983 has/have) and by 0.478 in gap under
`number_flip` (+5.403 against +4.925). Under `number_flip` the congruent and incongruent gaps
are +5.189 and +5.148; under `number_flip_all`, which keeps congruency, they are +6.370 and
+4.032.

## Files

| Path | What |
|---|---|
| `gate/{ioi,induction,factual,agreement}/{scheme}.json` (+ `.parquet` per prompt) | sections 3 and 10; one per (item, scheme) |
| `identity/ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0.json` (+ `.parquet`) | identity check, section 2 |
| `noise/{ioi,induction,agreement}/floor.json` | section 7 |
| `../../batteries/factual/survivors.json` | section 4 funnel, templates, survivors, partners |
