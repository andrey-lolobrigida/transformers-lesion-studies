# E1b — Task battery: gate, reference floor, noise floor

*Run 2026-09-23 on branch `phase-E1b-battery`, GPT-2 small at HF revision
`607a30d783dfa663caf39e06633721c8d4cfcd7e`. Survivor file written at repo commit `f1afd56`
(committed in `ad9dcd3`); gate artifacts at `ad9dcd3`; noise floors at `74a659a` (each
artifact's own `environment.repo_commit`). Interpretation
of the artifacts in this directory and of `batteries/factual/survivors.json`. Decisions:
D-013, D-014, the O-009 resolution; open question O-015.*

## 1. What this is

E1b builds the battery that E2 and E3 measure on: three items (IOI, induction, factual
recall), each with a clean/corrupt generator, a metric (`ld = logit[c] − logit[s]` at `END`),
a declared expected direction (`positive` for all three: damage is expected to lower `ld`)
and a corruption scheme whose `removes`/`inserts` are recorded in every artifact. The rules
it is measured against — the pre-registered clean-accuracy gate, the per-template reference
floor of 30, the statistical noise floor instead of a control item, filtering only for
factual recall — are recorded in D-014 and the O-009 resolution; the item order and the
agreement fallback in D-013. Everything below is measured on the clean model with no
intervention, except the noise floor (section 7), which is a mean-ablation sample.

## 2. Commands

Every artifact records its command, seed, n, BOS setting, model revision, library versions
and determinism flags. All runs use model revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`.

| What | Command | Seed / n |
|---|---|---|
| Factual survivor file | `uv run python -m src.lesion.counterfact` | greedy decoding, no seed; all 21,919 CounterFact records; no BOS; 10 generated tokens |
| Gate, all nine (item, scheme) pairs | `uv run python -m src.lesion.e1b_gate --item all` | seed 0; n = 2,000 for IOI and induction, n = 64 (every admitted survivor) for factual; reference-floor count at ref n = 1,000 (factual: 64), ref seed 0 |
| Identity against E0 | `uv run python -m src.lesion.ablate --battery ioi --component L0H0 --value zero --type node --positions all --direction ablate-clean --no-freeze --n 100000 --seed 0 --prepend-bos false --batch-size 512 --out-dir results/E1b/identity` | seed 0, n = 100,000, no BOS |
| Noise floor, IOI | `uv run python -m src.lesion.e1b_noise --item ioi` | seed 0, n = 2,000, ref n = 1,000, ref seeds 0–4, no BOS |
| Noise floor, induction | `uv run python -m src.lesion.e1b_noise --item induction` | seed 0, n = 2,000, ref n = 1,000, ref seeds 0–4, BOS prepended |

BOS defaults are per item (D-014 / E1b spec): no BOS for IOI (as in E0 and E1a) and factual
recall, BOS prepended for induction.

Every gate artifact carries a top-level `pre_registered` field: the gate CLI writes a
verdict only when the run is at the pre-registered seed 0 and n (2,000; all admitted
survivors for factual), and all three gated artifacts here have `pre_registered: true`.

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
| ioi | p_ABC | PASS | 2000 | 0.990 | +3.651 ± 0.036 | +0.062 | +3.590 ± 0.053 | 0.98 | 0.919 | 0.524 / 0.001 | 1.60 | 22 (5 below 30) |
| ioi | rand_names | extra | 2000 | 0.990 | +3.651 ± 0.036 | +0.039 | +3.613 ± 0.054 | 0.99 | 0.919 | 0.524 / 0.000 | 1.60 | 22 (5 below 30) |
| ioi | flip | extra | 2000 | 0.990 | +3.651 ± 0.036 | +3.632 | +0.019 ± 0.038 | 0.01 | 0.919 | 0.524 / 0.521 | 1.60 | 22 (5 below 30) |
| ioi | flip_rand | extra | 2000 | 0.990 | +3.651 ± 0.036 | +0.067 | +3.585 ± 0.056 | 0.98 | 0.919 | 0.524 / 0.000 | 1.60 | 22 (5 below 30) |
| ioi | repl_flip | extra | 2000 | 0.990 | +3.651 ± 0.036 | -3.642 | +7.293 ± 0.057 | 2.00 | 0.919 | 0.524 / 0.025 | 1.60 | 22 (5 below 30) |
| ioi | repl | extra | 2000 | 0.990 | +3.651 ± 0.036 | -3.597 | +7.248 ± 0.053 | 1.99 | 0.919 | 0.524 / 0.025 | 1.60 | 22 (5 below 30) |
| induction | fresh_prefix | PASS | 2000 | 0.999 | +17.005 ± 0.139 | -0.007 | +17.012 ± 0.138 | 1.00 | 0.974 | 0.768 / 0.000 | 6.22 | 37 (0 below 30) |
| factual | subject_swap | FAIL | 64 | 1.000 | +4.291 ± 0.312 | +0.187 | +4.104 ± 0.374 | 0.96 | 1.000 | 0.208 / 0.009 | 2.50 | 31 (0 below 30) |
| factual | subject_swap_sym | extra | 64 | 1.000 | +4.808 ± 0.293 | -2.676 | +7.484 ± 0.542 | 1.56 | 1.000 | 0.208 / 0.009 | 2.35 | 31 (0 below 30) |

Columns: fraction removed is `(mean clean ld − mean corrupt ld) / mean clean ld`; top-1 is
the rate at which `c` is the argmax over the full vocabulary on the clean prompt; the last
column is the smallest per-template count in a reference draw at ref n = 1,000 (factual:
64), ref seed 0, with the number of templates under the floor of 30.

Per default scheme, per condition:

- **IOI:** on `p_ABC`, n=2000, seed 0, no BOS, the clean pairwise accuracy is 0.990 against
  0.90 and the gap is +3.590 ± 0.053 logits against 1.0. PASS.
- **Induction:** on `fresh_prefix`, n=2000, seed 0, BOS prepended, the clean pairwise
  accuracy is 0.999 against 0.90 and the gap is +17.012 ± 0.138 logits against 1.0. PASS.
- **Factual recall:** on `subject_swap`, n=64, seed 0, no BOS, the clean pairwise accuracy
  is 1.000 against 0.90 and the gap is +4.104 ± 0.374 logits against 1.0; the admitted
  survivor count is 64 against 300. FAIL, on the survivor condition alone.

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
agreement addendum is pending the author. The failure is logged in the null-results table
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
ref seed 0.

- **IOI** (`p_ABC`, ref n = 1,000, 30 templates): minimum 22. **Five templates are below
  30:** ABBA/7 (22), ABBA/8 (28), ABBA/9 (28), BABA/1 (28), BABA/3 (25). At n = 1,000 the
  IOI reference does not meet the floor. The E1a MLP mean-ablation artifacts
  (`results/E1a/mlp/mean/`, the same `p_ABC` reference at n = 1,000, seed 0) record the
  same per-template counts. Which reference n E3 uses for IOI needs the author's decision;
  it is open as O-015 and is not chosen here.
- **Induction** (`fresh_prefix`, ref n = 1,000, 22 templates `i1`…`i22`): minimum 37, none
  below 30.
- **Factual recall** (`subject_swap`, ref n = 64, every admitted survivor, 2 templates):
  minimum 31, none below 30. Moot while the item's gate has failed.

## 7. Noise floor

Per passing item, default scheme, seed 0, n = 2,000: node mean ablation at all positions,
ablate-clean, reference n = 1,000 drawn from the default corrupt scheme and matched by
template, under reference seeds 0–4, for the 12 MLP layers and head 0 of each layer (24
components). Per component the floor is the larger of the standard deviation of
`effect_mean` across the five reference seeds and the per-prompt `sem` of the seed-0 run.

- **IOI** (`p_ABC`, no BOS): largest floor 0.0459, on L0.mlp, where the reference-seed spread
  dominates (spread 0.0459 against sem 0.0413). The spread dominates in 5 of the 24
  components (L0.mlp, L3.mlp, L6.mlp, L2H0, L4H0), the sem in the other 19.
- **Induction** (`fresh_prefix`, BOS prepended): largest floor 0.1419, on L0.mlp, where the
  sem dominates (sem 0.1419 against spread 0.0679). The sem dominates in all 24 components.
- **Factual recall:** no floor was measured, because its gate failed; `e1b_noise` refuses an
  item whose gate did not pass.

The rule for E3: **a heatmap cell under this item has to clear its component's floor, where
one was measured (the 24 components here); for other components E3 has to extend the
sample (spec, Risks).** The floor is measured under mean ablation at one reference size; it
is not measured for zero or resample ablation.

## 8. Obligation for later results docs

Per D-014 item 2, every later mean- or resample-ablation number cites, beside it, the
reference size and the fraction of the clean `ld` removed by the scheme its reference is
drawn from, taken from the table in section 3. For the two items that passed: `p_ABC`
removes 0.98 (IOI), `fresh_prefix` removes 1.00 (induction), each measured at n = 2,000,
seed 0.

## 9. What this does not show

- The gate is a clean-model sanity floor, not evidence of a circuit. Passing says the clean
  model separates `c` from `s` on these prompts and the corruption removes most of that
  separation; it says nothing about which components do it.
- Nothing here is a necessity or sufficiency claim. The noise-floor runs are mean
  ablations, but they are used only to size noise; no component's effect is interpreted.
- The noise floor is a sample of 24 components under 5 reference seeds, not the floor for
  every cell E3 will produce.
- The IOI extras describe output on corrupt prompts; they do not reproduce Wang et al.'s
  App. A fit or show how GPT-2 small uses position or token information.
- The factual-recall readings rest on n = 64 prompts in two templates; they are reported
  because they were measured, and the item's gate has failed.

## Files

| Path | What |
|---|---|
| `gate/{ioi,induction,factual}/{scheme}.json` (+ `.parquet` per prompt) | section 3; one per (item, scheme) |
| `identity/ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0.json` (+ `.parquet`) | identity check, section 2 |
| `noise/{ioi,induction}/floor.json` | section 7 |
| `../../batteries/factual/survivors.json` | section 4 funnel, templates, survivors, partners |
