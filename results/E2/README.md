# E2 — Reproduction

*Pre-registration committed before the first GPU run (D-015 item 2). Every
section after it is written once the runs exist. Rules: D-015. Spec:
`.superpowers/specs/2026-09-29-e2-reproduction-design.md` (untracked).*

## Pre-registration

This section mirrors the constant block at the top of
`src/lesion/e2_reproduce.py`; `tests/test_e2_reproduce.py` pins both. A
change to either after results exist is a new pre-registration and is logged
in `docs/04-decisions.md` first.

### Common settings

- n = 2,000 prompts, seed 0, GPT-2 small at HF revision `607a30d7`,
  TransformerLens 3.9.0. A verdict is written only at n = 2,000 and seed 0;
  every artifact records `pre_registered`.
- Mean references: corrupt side, template-matched, n = 2,000, seed 0 (O-015),
  except the ≈ 7-per-template bracket corners below.
- IOI: `p_IOI` against `p_ABC`, no BOS (D-011), 15 templates per order unless
  a corner says otherwise, (head, position) nodes (O-013). Induction:
  `fresh_prefix`, BOS prepended.
- Path patching: edge, Wang's convention (MLPs recompute), ablate-clean,
  the sender at the receiver's own position (any other position has no direct
  path; the driver refuses it).
- D-006: the source's value gates (resample for path patching, mean for
  knockouts, zero for I3); the other two values run beside, ungated.
- Sign-rule floor: F_ioi = `max_floor` of `results/E1b/noise/ioi/floor.json`
  (ref n 2,000, ref seeds 0–4).

### Wang et al.'s classes (26 heads)

| Class | Heads | Position | Source |
|---|---|---|---|
| `name_mover` | 9.6, 9.9, 10.0 | END | §3.1 |
| `negative_name_mover` | 10.7, 11.10 | END | §3.1 (position inferred: "same properties as Name Mover Heads") |
| `s_inhibition` | 7.3, 7.9, 8.6, 8.10 | END | §3, §3.2 |
| `induction` | 5.5, 5.8, 5.9, 6.9 | S2 | §3, §3.3; 5.8, 5.9 fuzzy (App. C), classed per App. K |
| `duplicate_token` | 0.1, 0.10, 3.0 | S2 | §3, §3.3; 0.10 fuzzy (App. C), classed per App. K |
| `previous_token` | 2.2, 4.11 | S1+1 | §3, App. D |
| `backup_name_mover` | 9.0, 9.7, 10.1, 10.2, 10.6, 10.10, 11.2, 11.9 | END | §3.4, App. F (position inferred: found by the END-position direct-effect sweep) |

### Induction targets

**I1 — evaluator rankings** [wang-2022 App. H, App. I]. 100 sequences of 100
ids uniform over the whole vocabulary, doubled to AA; gated: no BOS, no
exclusions, stimulus seed 0. Beside, ungated: the same draw with BOS; ranks
under stimulus seeds 1–4 and the per-head sd over seeds 0–4. Identity rule,
k = max(class size + 2, the source's stated rank):

| Row | Score | Published | Rule |
|---|---|---|---|
| `I1/previous_token` | previous-token (j → j−1, j = 1..199) | 4.11, 2.2 are the top two | top k = 4 |
| `I1/induction` | induction (j → j−99, j = 100..199) | 5.5, 6.9 among the top five | top k = 5 |
| `I1/duplicate` | duplicate (j → j−100, j = 100..199) | 3.0, 0.1 among the top three | top k = 4 |
| `I1/copy` | \|⟨z_j W_O, W_U[:, x_(j+1)]⟩\|, j = 100..198 (Fig. 17 orders by absolute value; signed beside) | 5.5, 6.9 among the 20 contributing most | top k = 20 |

**I2 — which induction mechanism (O-012).** Weight level, verdict `measured`:
Q-, K-, V-composition for every (earlier, later) head pair, minus a random
baseline (200 draws, seed 0, Gaussian factors of the same shapes); for 5.5 and
6.9, the scores with 4.11 and 2.2, above baseline or not, and their rank among
all earlier heads. Path level, on IOI, sign rule, resample from `p_ABC`:

| Route | Senders at | Receivers | Published | Expected |
|---|---|---|---|---|
| `k_route` | S1+1 | `k` of 5.5, 6.9 at S1+1 | 4.11, 2.2 lower ld (App. D, Fig. 13) | positive effect |
| `q_route` | S2 | `q` of 5.5, 6.9 at S2 | "did not find any significant effect" (App. D) | null |

**I3 — pattern-frozen ablation** (verdict `measured`). Heads 5.5, 6.9, 4.11,
2.2 singly and {5.5, 6.9} as a set; node, all positions, ablate-clean; zero
(Olsson's value) with mean and resample beside; each run frozen and unfrozen,
the delta reported (O-011).

**I4 — restore-clean** (verdict `measured`). Resample from the clean prompt
onto the `fresh_prefix` prompt: 5.5 and 6.9 at END, 4.11 and 2.2 at B1, singly
and as a set of four; fraction of the clean-minus-corrupt gap restored.

### IOI targets

**P1 — path-patching classes** (identity + sign), resample gated, zero and
mean beside. Candidates are the heads strictly below every receiver.

| Sweep | Senders at | Receiver | Candidates |
|---|---|---|---|
| `logits` | END | logits | 144 |
| `nm_queries` | END | `q` of 9.6, 9.9, 10.0 at END | 108 |
| `sinh_values` | S2 | `v` of 7.3, 7.9, 8.6, 8.10 at S2 | 84 |
| `ind_keys` | S1+1 | `k` of 5.5, 6.9 at S1+1 | 60 |

| Row | Sweep | Published | Rule |
|---|---|---|---|
| `P1/name_mover` | `logits` | 9.6, 9.9, 10.0 | top k = 5 |
| `P1/negative_name_mover` | `logits` | 10.7, 11.10 | bottom k = 4 |
| `P1/s_inhibition` | `nm_queries` | 7.3, 7.9, 8.6, 8.10 | top k = 6 |
| `P1/induction_duplicate` | `sinh_values` | 5.5, 6.9, 3.0, 0.1 | top k = 6 |
| `P1/previous_token` | `ind_keys` | 4.11, 2.2 | top k = 4 |
| `P1/name_mover/sign` | `logits` | each member positive | sign rule |
| `P1/negative_name_mover/sign` | `logits` | each member negative | sign rule |

Fuzzy heads 0.10, 5.8, 5.9: ranks in `sinh_values` reported, not gated.

**Bracket corners** for P2 and P3 (fixed: no BOS, (head, position) nodes,
template-matched means, seed 0, n = 2,000): `t15-ref210`, `t15-ref2000`,
`t7-ref98`, `t7-ref2000` — 15 or 7 templates per order × a reference of
≈ 7 per template (Miller et al.'s reading of Wang et al.; it breaks D-014's
floor of 30 and is labelled so) or 2,000 in total.

**P2 — Name Mover knockout** [wang-2022 §3.4, App. F]: mean-ablate 9.6, 9.9,
10.0 at END together; quantity (F(M) − F(K)) / F(M); published 0.05.
Contrast: the three heads' summed direct effects (edge to logits, mean, same
corner) over F(M); uninformative if the bracket overlaps their range over
the corners. Zero and resample beside, once per template mix.

**P3 — faithfulness** [wang-2022 §4]: complement knockout of the 26 nodes
(heads only; MLPs untouched), mean; gated quantity F(C)/F(M) as a ratio of
means; published 0.87; contrast 1.0. Beside: |F(M) − F(C)| (published 0.46),
the mean of per-prompt ratios and its IQR [miller-2024 §4.1–4.2]; zero and
resample, once per template mix.

**P4 — restore-clean** (verdict `measured`): clean activations onto the
`p_ABC` prompt, per class as a set at the class's position, then per head;
fraction of the gap restored. The sufficiency direction, which Wang did not run.

### Choices made in the plan, not in the spec

1. Negative and Backup Name Movers at END are inferred; fuzzy heads classed
   per App. K; Figure 2 (an image) not text-checked.
2. The I2 Q-route sender sits at S2 (at S1+1 the path is empty).
3. P1 candidates are the heads below every receiver.
4. The copy check ranks by absolute value (Fig. 17's order).
5. I1's stimulus size and averaging, as in the I1 table.
6. Composition scores on the weights as loaded (LayerNorm folded, centred),
   float64, cross-checked against TransformerLens.
7. P2's contrast is a range; any overlap makes the bracket uninformative.
   Published values are compared as points.
8. P1 sweeps are stored as per-sender aggregates.
9. A verdict is per entry; a sign entry is a conjunction over its class.
10. P4 restores Wang's seven classes, then the 26 heads singly.
11. P2/P3 siblings run once per template mix.

## Exit table

*Run 2026-09-29 on `phase-E2-reproduction`. Every section below this line was
written after the runs, from the committed artifacts; the Pre-registration
section above is unchanged since `4675ba6`. Heads are written `layer.head`
(the artifacts write `L9H9`).*

Conventions for every number below. **Effect** is the artifacts' `effect_mean`:
the mean over prompts of (`ld` without the intervention − `ld` with it), so a
positive effect means the intervention lowers the mean logit difference and a
negative one means it raises it. **Fraction restored** (I4, P4) is (mean `ld`
with the clean activations written in − mean corrupt `ld`) / (mean clean `ld` −
mean corrupt `ld`). **Fraction removed** is the share of the clean `ld` that
the reference scheme removes (D-014 item 2): `p_ABC` 0.983 at 15 templates per
order and 0.961 at 7 per order; `fresh_prefix` 1.000 (each target's
`result.context`). IOI runs have no BOS; induction runs have BOS prepended.

`ours` is a rank (identity rows), an effect in logits (sign rows), a
fraction-of-`F(M)` bracket (P2, P3), a composition score minus the random
baseline (I2 composition), the frozen zero-ablation effect (I3), or a
fraction restored (I4, P4).

| id | published | ours | tolerance | verdict |
|---|---|---|---|---|
| `I1/previous_token` | 4.11, 2.2 in the top 2 | 4.11: 1; 2.2: 4 | top k = 4 of 144 | matched |
| `I1/induction` | 5.5, 6.9 in the top 5 | 5.5: 2; 6.9: 3 | top k = 5 of 144 | matched |
| `I1/duplicate` | 3.0, 0.1 in the top 3 | 3.0: 2; 0.1: 3 | top k = 4 of 144 | matched |
| `I1/copy` | 5.5, 6.9 in the top 20 | 5.5: 16; 6.9: 5 | top k = 20 of 144 | matched |
| `I2/composition` | — | 4.11→5.5: K +0.0611, Q +0.0068; 2.2→5.5: K +0.0339, Q +0.0153; 4.11→6.9: K +0.0674, Q +0.0145; 2.2→6.9: K +0.0349, Q +0.0137 | measured; score minus the random baseline | measured |
| `I2/k_route/L4H11` | lowers ld (significant) | +0.4794 | \|effect\| vs max(2 sem, F_ioi = 0.0404) | matched |
| `I2/k_route/L2H2` | lowers ld (significant) | +0.1263 | \|effect\| vs max(2 sem, F_ioi = 0.0404) | matched |
| `I2/q_route/L4H11` | no significant effect | +0.0004 | \|effect\| vs max(2 sem, F_ioi = 0.0404) | matched |
| `I2/q_route/L2H2` | no significant effect | +0.0115 | \|effect\| vs max(2 sem, F_ioi = 0.0404) | matched |
| `I3/pattern_frozen_ablation` | — | 5.5: −0.2005; 6.9: −0.7099; 4.11: −0.2897; 2.2: −0.2233; {5.5, 6.9}: −0.6485 (zero, frozen) | measured; frozen with the unfrozen twin beside (O-011) | measured |
| `I4/restore_clean` | — | 5.5@END: 0.0235; 6.9@END: 0.0721; 4.11@B1: −0.0003; 2.2@B1: −0.0000; set of four: 0.1086 | measured; fraction of the gap restored | measured |
| `P1/name_mover` | 9.6, 9.9, 10.0 | 9.6: 2; 9.9: 1; 10.0: 3 | top k = 5 of 144 | matched |
| `P1/negative_name_mover` | 10.7, 11.10 | 10.7: 1; 11.10: 2 | bottom k = 4 of 144 | matched |
| `P1/s_inhibition` | 7.3, 7.9, 8.6, 8.10 | 7.3: 4; 7.9: 3; 8.6: 1; 8.10: 2 | top k = 6 of 108 | matched |
| `P1/induction_duplicate` | 5.5, 6.9, 3.0, 0.1 | 5.5: 1; 6.9: 3; 3.0: 2; 0.1: 4 | top k = 6 of 84 | matched |
| `P1/previous_token` | 4.11, 2.2 | 4.11: 1; 2.2: 2 | top k = 4 of 60 | matched |
| `P1/name_mover/sign` | positive direct effect for each member | 9.6: +0.9559; 9.9: +2.5218; 10.0: +0.7357 | each member: sign and \|effect\| > max(2 sem, F_ioi = 0.0404) | matched |
| `P1/negative_name_mover/sign` | negative direct effect for each member | 10.7: −1.4962; 11.10: −0.8194 | each member: sign and \|effect\| > max(2 sem, F_ioi = 0.0404) | matched |
| `P2/nm_knockout_drop` | 0.05 | [0.0038, 0.0130] | bracket over four corners; uninformative if it overlaps the contrast's range | **not matched** |
| `P3/faithfulness` | 0.87 | [0.8513, 0.9030] | bracket over four corners; contrast 1.0 | matched |
| `P4/restore_clean` | — | name_mover@END: 1.2293; negative_name_mover@END: −0.6689; s_inhibition@END: 0.1600; induction@S2: 0.0011; duplicate_token@S2: −0.0274; previous_token@S1+1: −0.0054; backup_name_mover@END: 0.2950 | measured; fraction of the gap restored | measured |

Counts (`results/E2/verdicts.json`, 21 entries, none missing, every one
`pre_registered: true`): **matched 16, measured 4, not matched 1** (P2),
bracketed, uninformative 0.

Pre-registration: commit `4675ba6`; every verdict at n = 2,000, seed 0 (I1
uses its own stimulus, 100 sequences at stimulus seed 0; the I2 composition
scores are computed on the weights, with the random baseline at seed 0).

## Validation gates

Run before any result, as hard stops (spec, Validation; plan Task 8):
`uv run pytest -q -m slow tests/test_e2_gates.py` → **14 passed** on the RTX
5060 with GPT-2 small at revision `607a30d7`:

- the multi-component mean reference equals `reference.py`'s for a single
  head, bitwise, on IOI and induction (2 tests);
- a one-member set equals the single-component node run, bitwise, under
  zero, mean and resample, on IOI and induction, with and without pattern
  freezing (9 tests);
- an empty set equals the clean pass, bitwise, on IOI and induction (2 tests);
- the composition scores agree with TransformerLens's (`allclose`, 1 test).

All passed on the first run, so nothing stopped. An end-to-end smoke run of
every target at n = 64 (`--out-dir scratch/e2-smoke`, gitignored) completed
with every entry-level verdict `null`, as the `pre_registered` rule requires;
its numbers are not results and were not read. The fast tier
(`uv run pytest -q -m "not slow"`) passed before and after.

Two code changes were made after the pre-registration commit, both below the
`END OF PRE-REGISTRATION` line of `src/lesion/e2_reproduce.py` and before the
first GPU run: the sign and magnitude verdict rules refuse non-finite inputs
(`6c464c4`), and the P1 verdict entries carry the mean reference size and its
per-template counts (`869a833`, D-014). The constant block and this README's
Pre-registration section are unchanged. The untouched modules
(`interventions.py`, `runner.py`, `reference.py`, `spec.py`) have no diff
against `v-E1b`, and no source or test file changed between the gate commit
(`52dcb87`) and the last run.

## Induction

### I1 — Evaluator rankings [wang-2022 App. H, App. I]

Setting: GPT-2 small, no intervention; 100 sequences of 100 token ids drawn
uniformly over the whole vocabulary with replacement, each doubled to `AA`
(200 positions), no BOS, no exclusions, stimulus seed 0. Scores as defined in
the Pre-registration table; the copy score is `⟨z_j W_O, W_U[:, x_(j+1)]⟩`
without `b_O` or the final LayerNorm, ranked by absolute value. Each row ranks
all 144 heads. Beside, ungated: the same draw with BOS prepended, stimulus
seeds 1–4, and each member's score sd over seeds 0–4.

| Row | Member | Score (seed 0) | Rank (gated) | Rank, BOS | Ranks, seeds 1–4 | sd over seeds 0–4 | k | Verdict |
|---|---|---|---|---|---|---|---|---|
| previous-token | 4.11 | 0.9887 | 1 | 1 | 1, 1, 1, 1 | 0.0004 | 4 | matched |
| | 2.2 | 0.4847 | 4 | 4 | 4, 4, 4, 4 | 0.0011 | | |
| induction | 5.5 | 0.9279 | 2 | 2 | 2, 2, 2, 2 | 0.0010 | 5 | matched |
| | 6.9 | 0.9224 | 3 | 3 | 3, 3, 3, 3 | 0.0013 | | |
| duplicate | 3.0 | 0.6454 | 2 | 2 | 2, 2, 2, 2 | 0.0028 | 4 | matched |
| | 0.1 | 0.1468 | 3 | 3 | 3, 3, 3, 3 | 0.0001 | | |
| copy (\|·\|) | 5.5 | 4.671 | 16 | 16 | 16, 16, 16, 16 | 0.024 | 20 | matched |
| | 6.9 | 17.698 | 5 | 6 | 5, 5, 5, 5 | 0.049 | | |

The heads the rows rank above or among the members (`result.top_k`):

- previous-token (top 4): 4.11 0.9887, 3.7 0.5357, 6.8 0.4937, 2.2 0.4847.
  Published: 4.11 and 2.2 are the top two; here 2.2 is fourth, inside k = 4.
- induction (top 5): 5.1 0.9369, 5.5 0.9279, 6.9 0.9224, 7.10 0.9077,
  7.2 0.8345.
- duplicate (top 4): 0.5 0.7044, 3.0 0.6454, 0.1 0.1468, 7.1 0.0499.
- copy (top 20, by absolute value): 7.2, 9.9, 9.6, 7.10, 6.9 (5th), 10.0,
  10.7, 10.1, 11.9, 5.1, 11.10, 10.6, 10.10, 8.1, 10.11, 5.5 (16th), 7.1, 9.0,
  5.0, 9.1 (2.998, the cut). The signed ranking puts 5.5 at 14 and 6.9 at 5.

No tie at any cut. These are attention and output statistics on a synthetic
stimulus, not interventions; they say where the heads rank under our
operationalisation of Wang's scores (averaging and positions fixed in the
artifact, `I1/scores.json` `definitions`), not that the heads perform a
function.

### I2 — Composition scores and the K/Q routes (O-012)

**Weight level (verdict `measured`).** Q-, K- and V-composition scores
[elhage-2021] for every (earlier, later) head pair, on the weights as loaded
(TransformerLens defaults: LayerNorm folded, writing weights and unembedding
centred), exact norms, minus a random baseline: 200 draws of Gaussian factors
of the same shapes, seed 0 (Q mean 0.03607, sd 0.00044; K mean 0.03607, sd
0.00043; V mean 0.03609, sd 0.00042). Rank is among all heads in earlier
layers (60 for layer 5, 72 for layer 6).

| Pair | K − baseline (rank) | Q − baseline (rank) | V − baseline (rank) |
|---|---|---|---|
| 4.11 → 5.5 | +0.0611 (1 of 60) | +0.0068 (15 of 60) | +0.0226 (4 of 60) |
| 2.2 → 5.5 | +0.0339 (6 of 60) | +0.0153 (5 of 60) | +0.0040 (34 of 60) |
| 4.11 → 6.9 | +0.0674 (1 of 72) | +0.0145 (4 of 72) | +0.0043 (18 of 72) |
| 2.2 → 6.9 | +0.0349 (6 of 72) | +0.0137 (7 of 72) | −0.0062 (63 of 72) |

All K and Q entries are above the baseline mean; the only entry below it is
V-composition 2.2 → 6.9.

**Path level (gated, sign rule).** On ioi/`p_IOI` corrupted with `p_ABC`,
n = 2,000, seed 0, no BOS; edge path patching, Wang convention (MLPs
recompute), ablate-clean, patterns not frozen; one run per sender, with 5.5
and 6.9 as joint receivers. Clean mean `ld` 3.6514; fraction removed 0.983.
F_ioi = 0.0404 (`results/E1b/noise/ioi/floor.json` `max_floor`, ref n 2,000).
The mean sibling uses a template-matched corrupt-side reference, ref n 2,000,
per-template minimum 52.

| Route | Sender | Resample (gated) | Zero (beside) | Mean (beside; ref n 2,000, min 52) | Bound | Verdict |
|---|---|---|---|---|---|---|
| K: sender at S1+1 → `k` of 5.5, 6.9 at S1+1 | 4.11 | +0.4794 ± 0.0085 | +0.1615 ± 0.0036 | +0.2767 ± 0.0048 | 0.0404 (floor) | matched |
| | 2.2 | +0.1263 ± 0.0034 | +0.0404 ± 0.0014 | +0.0839 ± 0.0020 | 0.0404 (floor) | matched |
| Q: sender at S2 → `q` of 5.5, 6.9 at S2 | 4.11 | +0.0004 ± 0.0001 | +0.0018 ± 0.0006 | +0.0003 ± 0.0002 | 0.0404 (floor) | matched (null) |
| | 2.2 | +0.0115 ± 0.0004 | +0.0198 ± 0.0006 | +0.0112 ± 0.0004 | 0.0404 (floor) | matched (null) |

In rule-1 form: under resample path patching (edge, Wang convention,
ablate-clean, unfrozen) on ioi/`p_ABC`, n = 2,000, seed 0, patching the path
4.11 → `k` of 5.5 and 6.9 at S1+1 lowers mean `ld` by 0.4794 ± 0.0085, and the
path 2.2 → the same keys by 0.1263 ± 0.0034; F_ioi = 0.0404; fraction removed
0.983. The paths 4.11 → `q` of 5.5 and 6.9 at S2 and 2.2 → the same queries
change mean `ld` by +0.0004 ± 0.0001 and +0.0115 ± 0.0004, inside the bound.

The Q-route verdict is `matched` on a published null: it shows only that this
measurement also found no effect above the bound, not that the route is
absent. Both Q-route effects are nonzero relative to their own sem (2.2:
0.0115 ± 0.0004, about 28 sem; 4.11: 0.0004 ± 0.0001, about 3.8 sem); they
count as null only relative to the bound max(2 sem, F_ioi) = 0.0404, whose
floor F_ioi was measured under node mean ablation of 24 other components,
not on these heads or on path patching. Under the ungated zero sibling, the 2.2 K-route effect (0.04041) sits
just below the floor (0.04043), so it would not clear the sign rule there;
under resample and mean it does. That disagreement between values is reported,
not resolved (epistemic rule 3).

### I3 — Pattern-frozen ablation (O-011)

Setting: induction/`fresh_prefix`, n = 2,000, seed 0, BOS prepended; node
ablation at all positions, ablate-clean. **Frozen**: every attention pattern
pinned to the clean run's (Olsson et al.'s pattern-preserving ablation);
**unfrozen**: patterns recompute. Zero is the source's value; mean
(template-matched corrupt-side reference, ref n 2,000, per-template minimum 71
over 22 templates) and resample run beside. Clean mean `ld` 17.005; fraction
removed 1.000. Delta = frozen effect − unfrozen effect.

| Unit | Value | Frozen effect | Unfrozen effect | Delta |
|---|---|---|---|---|
| 5.5 | zero | −0.2005 ± 0.0209 | +1.5622 ± 0.0378 | −1.7627 |
| | mean | +0.1065 ± 0.0176 | +0.5174 ± 0.0302 | −0.4108 |
| | resample | +0.1241 ± 0.0182 | +0.5560 ± 0.0312 | −0.4319 |
| 6.9 | zero | −0.7099 ± 0.0230 | +0.4532 ± 0.0274 | −1.1631 |
| | mean | −0.1298 ± 0.0189 | +0.8040 ± 0.0292 | −0.9338 |
| | resample | −0.1153 ± 0.0199 | +0.8130 ± 0.0299 | −0.9283 |
| 4.11 | zero | −0.2897 ± 0.0140 | +3.1665 ± 0.0611 | −3.4562 |
| | mean | −0.3458 ± 0.0125 | +3.2085 ± 0.0605 | −3.5543 |
| | resample | +0.0787 ± 0.0139 | +5.2479 ± 0.0820 | −5.1692 |
| 2.2 | zero | −0.2233 ± 0.0076 | +0.1457 ± 0.0185 | −0.3690 |
| | mean | −0.2496 ± 0.0076 | +0.0476 ± 0.0180 | −0.2972 |
| | resample | −0.0876 ± 0.0075 | +0.2238 ± 0.0195 | −0.3115 |
| {5.5, 6.9} | zero | −0.6485 ± 0.0365 | +2.5815 ± 0.0542 | −3.2300 |
| | mean | +1.0459 ± 0.0401 | +2.8796 ± 0.0650 | −1.8337 |
| | resample | +1.0907 ± 0.0409 | +2.9429 ± 0.0665 | −1.8522 |

In rule-1 form, the gated value: under zero, node, ablate-clean, patterns
frozen, on induction/`fresh_prefix`, n = 2,000, seed 0, ablating the set
{5.5, 6.9} at all positions raises mean `ld` by 0.648 ± 0.036; its unfrozen
twin lowers it by 2.581 ± 0.054. Under frozen zero ablation every one of the
five units raises mean `ld` (by 0.20 to 0.71); under unfrozen zero ablation
every one lowers it (by 0.15 to 3.17). Under frozen mean and resample, the
set {5.5, 6.9} lowers mean `ld` by 1.046 ± 0.040 and 1.091 ± 0.041
(ref n 2,000, minimum 71, fraction removed 1.000 beside both). Every delta in
the table is negative.

Olsson et al.'s expectation, stated as coming from other models and not as a
published GPT-2 small claim (`result.olsson_expectation`): ablating induction
heads damages induction. Under frozen zero ablation, the value that
expectation comes with, the measured sign is the opposite for all five units
here; under the unfrozen twin, and under frozen mean and resample for the
set, it is the expected sign. The verdict is `measured`; there is no
published number to match. The delta has no standard error of its own in
the artifact (the frozen and unfrozen runs share prompts, but their
covariance was not computed).

The frozen sign is not specific to zero. Under frozen ablation, per the
artifact (`result.table`), the units that raise mean `ld` are: under zero,
all five; under mean, 6.9 (by 0.1298 ± 0.0189), 4.11 (0.3458 ± 0.0125) and
2.2 (0.2496 ± 0.0076); under resample, 6.9 (0.1153 ± 0.0199) and 2.2
(0.0876 ± 0.0075). Under frozen mean and resample, 5.5 (by 0.1065 ± 0.0176
and 0.1241 ± 0.0182) and the set {5.5, 6.9} lower it, and so does 4.11 under
frozen resample (by 0.0787 ± 0.0139). The sign opposite to Olsson et al.'s
expectation therefore holds for 6.9 and 2.2 under all three values, for 4.11
under zero and mean, and for 5.5 and the set under zero only.

Epistemic rule 7 asks for variation of the ablation method, the prompt
template and the corruption scheme before a surprising result is believed.
Only the first is done here (three values, frozen and unfrozen). The other
two are not possible inside E2: the induction battery has one corruption
scheme (`InductionBattery.schemes == ("fresh_prefix",)`,
`src/lesion/induction.py`) and one prompt construction (repeated random
tokens). Remaining checks, proposed for the author and neither run nor
planned in detail here:

- a second corruption scheme or prompt construction for induction;
- ablation at END only against ablation at all positions (I3 ablates at all
  positions; I4's END-only restore-clean of 5.5 and 6.9 recovers 0.0235 and
  0.0721 of the gap, a sufficiency reading in the other direction, so it does
  not stand in for an END-only ablation).

### I4 — Restore-clean on induction

Setting: induction, the `fresh_prefix` prompt as destination, n = 2,000,
seed 0, BOS prepended; node, restore-clean, the clean prompt's activations
written in (resample from the clean prompt), patterns not frozen. Clean mean
`ld` 17.005, corrupt −0.007, gap 17.012; fraction removed 1.000. No zero or
mean sibling: the target was pre-registered with clean activations only.

| Unit | Position | Effect | Mean `ld` after restoring | Fraction restored |
|---|---|---|---|---|
| 5.5 | END | −0.4005 ± 0.0106 | 0.393 | 0.0235 |
| 6.9 | END | −1.2271 ± 0.0149 | 1.220 | 0.0721 |
| 4.11 | B1 | +0.0059 ± 0.0053 | −0.013 | −0.0003 |
| 2.2 | B1 | +0.00005 ± 0.00058 | −0.007 | −0.0000 |
| set of four | as above | −1.8480 ± 0.0276 | 1.841 | 0.1086 |

This is the sufficiency direction. Under resample restore-clean (node,
unfrozen) on induction/`fresh_prefix`, n = 2,000, seed 0, restoring the clean
output of 6.9 at END recovers 0.072 of the clean-minus-corrupt gap; 5.5 at
END recovers 0.024; 4.11 and 2.2 at B1 recover none to three decimals
(effects 1.1 and 0.1 sem from zero); the four together recover 0.109. These fractions say how much of the
gap writing in these activations brings back on this prompt pair; they are
not statements about what removing the heads does (I3 is that).

## IOI

Setting for every IOI number: ioi/`p_IOI` corrupted with `p_ABC`, n = 2,000,
seed 0, no BOS, (head, position) nodes, template-matched corrupt-side means.
At 15 templates per order the clean mean `ld` is 3.6514 and the corrupt
0.0619 (fraction removed 0.983); at 7 per order, 3.4754 and 0.1350 (0.961).
F_ioi = 0.0404.

### P1 — Path-patching classes (identity and sign)

Setting: edge path patching, Wang convention (MLPs recompute), ablate-clean,
patterns not frozen; resample gated, zero and mean beside (mean: ref n 2,000,
per-template minimum 52); 15 templates per order. Candidates are the heads
strictly below every receiver. The score is the effect.

**Operationalisation (`result.operationalisation`, verbatim):** "ranking by
path-patching effect; Wang et al. selected classes from path-patching figures
plus follow-up tests". A `matched` here means the published members rank
inside k under this ranking; it is not a reproduction of Wang et al.'s
selection procedure.

| Class | Sweep (candidates) | Members: rank (resample) | Top k by resample effect | Ranks under zero / mean (ungated) | Verdict |
|---|---|---|---|---|---|
| Name Mover | `logits` (144) | 9.9: 1, 9.6: 2, 10.0: 3 | 9.9 +2.522, 9.6 +0.956, 10.0 +0.736, 10.10 +0.463, 10.6 +0.270 (k = 5) | same / same | matched |
| Negative Name Mover | `logits` (144), from the bottom | 10.7: 1, 11.10: 2 | 10.7 −1.496, 11.10 −0.819, 11.2 −0.375, 9.8 −0.037 (k = 4) | same / same | matched |
| S-Inhibition | `nm_queries` (108) | 8.6: 1, 8.10: 2, 7.9: 3, 7.3: 4 | 8.6 +0.477, 8.10 +0.367, 7.9 +0.316, 7.3 +0.183, 6.1 +0.022, 8.3 +0.005 (k = 6) | same / same | matched |
| Induction + Duplicate | `sinh_values` (84) | 5.5: 1, 3.0: 2, 6.9: 3, 0.1: 4 | 5.5 +1.282, 3.0 +0.468, 6.9 +0.407, 0.1 +0.192, 3.4 +0.081, 5.1 +0.048 (k = 6) | zero: 0.1 at **17**, others same / same | matched |
| Previous-token | `ind_keys` (60) | 4.11: 1, 2.2: 2 | 4.11 +0.479, 2.2 +0.126, 3.7 +0.062, 3.3 +0.043 (k = 4) | zero: 2.2 at **10** / same | matched |

Fuzzy heads, reported and not gated, ranks in `sinh_values` under resample:
0.10 at 79, 5.8 at 15, 5.9 at 10 of 84.

Under the ungated zero sibling two members fall outside k: 0.1 ranks 17 of 84
in `sinh_values` and 2.2 ranks 10 of 60 in `ind_keys`. The verdict is at
resample, Wang's value; the zero ranks are a disagreement between values and
are reported as such (epistemic rule 3). The previous-token sweep's 4.11 and
2.2 resample effects are the I2 K-route runs, bitwise (checked at Task 12).

**Sign.** In rule-1 form: under resample path patching (edge, Wang
convention, ablate-clean, unfrozen) on ioi/`p_ABC`, n = 2,000, seed 0,
patching the path from each head at END to the logits changes mean `ld` by:

| Head | Resample (gated) | Bound | Zero (beside) | Mean (beside; ref n 2,000, min 52) | Verdict |
|---|---|---|---|---|---|
| 9.6 | +0.9559 ± 0.0179 | 0.0404 (floor) | +0.9507 | +0.9442 | matched |
| 9.9 | +2.5218 ± 0.0259 | 0.0517 (2 sem) | +2.5030 | +2.5052 | matched |
| 10.0 | +0.7357 ± 0.0171 | 0.0404 (floor) | +0.6942 | +0.7221 | matched |
| 10.7 | −1.4962 ± 0.0209 | 0.0418 (2 sem) | −1.4186 | −1.5198 | matched |
| 11.10 | −0.8194 ± 0.0141 | 0.0404 (floor) | −0.8297 | −0.8185 | matched |

Positive: patching the path lowers mean `ld` (Name Movers); negative: it
raises it (Negative Name Movers). All three values agree in sign for every
member. Fraction removed 0.983 beside every resample and mean number.

### P2 — Name Mover knockout [wang-2022 §3.4, App. F] — not matched

Quantity: (F(M) − F(K)) / F(M), with K the model with 9.6, 9.9 and 10.0
mean-ablated together at END (node, ablate-clean, unfrozen, set knockout).
Published: 0.05. Contrast: the three heads' single-head direct effects (edge
to logits, Wang convention, mean, same corner) summed, over F(M) — a sum, not
a joint edge ablation. The ≈ 7-per-template corners (`t15-ref210`, `t7-ref98`)
are **below D-014's floor of 30 (Miller et al.'s reading of Wang et al.)**.

| Corner | Ref n (per-template min) | F(M) | Knockout effect | Quantity | Direct effects 9.6 / 9.9 / 10.0 | Contrast |
|---|---|---|---|---|---|---|
| `t15-ref210` — below D-014's floor of 30 (Miller et al.'s reading of Wang et al.) | 210 (2) | 3.6514 | +0.0475 ± 0.0183 | 0.0130 | 0.9427 / 2.5074 / 0.7235 | 1.1430 |
| `t15-ref2000` | 2,000 (52) | 3.6514 | +0.0137 ± 0.0181 | 0.0038 | 0.9442 / 2.5052 / 0.7221 | 1.1425 |
| `t7-ref98` — below D-014's floor of 30 (Miller et al.'s reading of Wang et al.) | 98 (3) | 3.4754 | +0.0382 ± 0.0175 | 0.0110 | 0.8892 / 2.3060 / 0.7124 | 1.1244 |
| `t7-ref2000` | 2,000 (121) | 3.4754 | +0.0350 ± 0.0171 | 0.0101 | 0.8939 / 2.3063 / 0.7147 | 1.1265 |

Bracket [0.0038, 0.0130], width 0.0093. Contrast range [1.1244, 1.1430]: the
bracket does not overlap it, so the verdict is not `bracketed, uninformative`.
**The published 0.05 lies outside the bracket, above its upper end by 0.037.
Verdict: not matched.** Fraction removed 0.983 (15 per order) and 0.961
(7 per order) beside every corner.

In rule-1 form: under mean, node, ablate-clean, unfrozen, on ioi/`p_ABC`,
n = 2,000, seed 0, no BOS, mean-ablating 9.6, 9.9 and 10.0 together at END
lowers mean `ld` by between 0.0137 ± 0.0181 and 0.0475 ± 0.0183 logits across
the four corners, which is 0.0038 to 0.0130 of F(M); the published value is
0.05 [wang-2022 §3.4, App. F].
The knockout effects are 0.8 to 2.6 sem from zero (0.0137 ± 0.0181 at
`t15-ref2000` is within one sem). Restricted to the two
corners that meet the floor, the range is [0.0038, 0.0101], also below 0.05.

Siblings, ungated, once per template mix:

| Mix | Value | Knockout effect | Quantity |
|---|---|---|---|
| 15 per order | zero | −0.0896 ± 0.0192 | −0.0245 |
| 15 per order | resample | +0.1988 ± 0.0199 | 0.0544 |
| 7 per order | zero | −0.0692 ± 0.0179 | −0.0199 |
| 7 per order | resample | +0.1920 ± 0.0190 | 0.0552 |

The resample siblings are not the source's value (mean, per the
pre-registration) and do not enter the verdict. Under zero the knockout
raises mean `ld`. What the artifacts show: at Wang's value, over the four
pre-registered corners, the drop is 0.4% to 1.3% of F(M), not 5%. They do not
show why.

Under the ungated resample sibling the quantity is 0.0544 (15 per order) and
0.0552 (7 per order), both above the published 0.05; under the ungated zero
sibling it is −0.0245 and −0.0199. The gated verdict is at mean, Wang's
stated value, where the bracket is [0.0038, 0.0130]. The disagreement between
ablation values is reported, not resolved (epistemic rule 3); the verdict
stays `not matched`.

The pre-registered contrast (spec §P2: the total drop is far below the summed
direct effect) is the relation observed: bracket [0.0038, 0.0130] against a
contrast range of [1.1244, 1.1430]. This does not change the verdict against
the published 0.05, which is `not matched`.

### P3 — Faithfulness [wang-2022 §4]

Quantity: F(C)/F(M) as a ratio of means, with C the model in which every head
node **outside** the 26 circuit nodes is mean-ablated (complement knockout,
heads only, MLPs untouched; each circuit head kept at its class's position;
node, ablate-clean, unfrozen). Published: 0.87. Contrast: 1.0.

| Corner | Ref n (per-template min) | F(M) | F(C) | F(C)/F(M) (gated) | \|F(M) − F(C)\| | Mean of per-prompt ratios (IQR) |
|---|---|---|---|---|---|---|
| `t15-ref210` — below D-014's floor of 30 (Miller et al.'s reading of Wang et al.) | 210 (2) | 3.6514 | 3.1084 | 0.8513 | 0.5429 ± 0.0295 | 1.2297 (0.6378–1.0844) |
| `t15-ref2000` | 2,000 (52) | 3.6514 | 3.2390 | 0.8871 | 0.4124 ± 0.0289 | 1.3231 (0.6731–1.1212) |
| `t7-ref98` — below D-014's floor of 30 (Miller et al.'s reading of Wang et al.) | 98 (3) | 3.4754 | 2.9640 | 0.8528 | 0.5114 ± 0.0278 | 0.8849 (0.6374–1.1020) |
| `t7-ref2000` | 2,000 (121) | 3.4754 | 3.1383 | 0.9030 | 0.3370 ± 0.0271 | 0.9623 (0.6841–1.1589) |

Bracket [0.8513, 0.9030], width 0.0517; the contrast 1.0 is outside it, and
the published 0.87 is inside. **Verdict: matched.** Beside, ungated:
|F(M) − F(C)| spans 0.337–0.543 against a published 0.46; the mean of
per-prompt ratios spans 0.885–1.323 [miller-2024 §4.1–4.2], and in the two
15-per-order corners it lies above the upper quartile. Fraction removed 0.983
(15 per order) and 0.961 (7 per order).

In rule-1 form: under mean, node, ablate-clean, unfrozen, on ioi/`p_ABC`,
n = 2,000, seed 0, no BOS, knocking out the complement of the 26 circuit
heads keeps F(C)/F(M) at 0.851 to 0.903 across the four corners; the
published value is 0.87 [wang-2022 §4].

The match depends on the corners below the floor. The two corners at ref n
2,000 give 0.8871 and 0.9030; that range, [0.8871, 0.9030], does not contain
0.87. The two ≈ 7-per-template corners — below D-014's floor of 30 (Miller et
al.'s reading of Wang et al.) — give 0.8513 and 0.8528, and those set the
bracket's lower end. The verdict follows the pre-registered four-corner rule
and stands as `matched`; this paragraph records what it rests on. Across the
corners, F(C)/F(M) moves by 0.036–0.050 with reference size (0.8513 → 0.8871
at 15 per order, 0.8528 → 0.9030 at 7 per order) and by at most 0.016 with
template mix (0.0015 at the ≈ 7-per-template reference, 0.0159 at 2,000).

Siblings, ungated, once per template mix: zero F(C)/F(M) −0.0155 (15 per
order) and −0.0140 (7 per order), F(C) −0.057 and −0.049; resample 0.5855 and
0.5884.

### P4 — Restore-clean on IOI

The sufficiency direction Wang et al. did not run. Setting: the `p_ABC` prompt
as destination, node, restore-clean, the clean prompt's activations written in
(resample from the clean prompt), unfrozen, 15 templates per order; each
class restored as a set at its class's position, then each of the 26 heads
singly. Corrupt mean `ld` 0.0619, clean 3.6514, gap 3.5895; fraction removed
0.983. No zero or mean sibling: pre-registered with clean activations only.

Per class (members as in the Pre-registration table):

| Class @ position | Effect | Mean `ld` after restoring | Fraction restored |
|---|---|---|---|
| name_mover @ END | −4.4128 ± 0.0437 | 4.4746 | 1.2293 |
| negative_name_mover @ END | +2.4011 ± 0.0305 | −2.3393 | −0.6689 |
| s_inhibition @ END | −0.5744 ± 0.0156 | 0.6362 | 0.1600 |
| induction @ S2 | −0.0040 ± 0.0066 | 0.0658 | 0.0011 |
| duplicate_token @ S2 | +0.0982 ± 0.0095 | −0.0363 | −0.0274 |
| previous_token @ S1+1 | +0.0192 ± 0.0008 | 0.0426 | −0.0054 |
| backup_name_mover @ END | −1.0589 ± 0.0284 | 1.1208 | 0.2950 |

Per head (fraction restored; effect ± sem in parentheses):

| Class | Heads |
|---|---|
| Name Mover @ END | 9.6 0.2921 (−1.0486 ± 0.0193); 9.9 0.6994 (−2.5106 ± 0.0246); 10.0 0.2351 (−0.8440 ± 0.0195) |
| Negative Name Mover @ END | 10.7 −0.4413 (+1.5841 ± 0.0215); 11.10 −0.2349 (+0.8430 ± 0.0144) |
| S-Inhibition @ END | 7.3 0.0326 (−0.1169 ± 0.0047); 7.9 0.0562 (−0.2018 ± 0.0045); 8.6 −0.0059 (+0.0211 ± 0.0069); 8.10 0.0684 (−0.2456 ± 0.0056) |
| Induction @ S2 | 5.5 −0.0001 (+0.0004 ± 0.0059); 5.8 −0.0001 (+0.0004 ± 0.0010); 5.9 0.0019 (−0.0068 ± 0.0020); 6.9 −0.0001 (+0.0003 ± 0.0012) |
| Duplicate Token @ S2 | 0.1 −0.0424 (+0.1521 ± 0.0050); 0.10 −0.0027 (+0.0097 ± 0.0016); 3.0 −0.0030 (+0.0108 ± 0.0031) |
| Previous Token @ S1+1 | 2.2 −0.0016 (+0.0057 ± 0.0003); 4.11 −0.0037 (+0.0134 ± 0.0006) |
| Backup Name Mover @ END | 9.0 0.0253; 9.7 0.0418; 10.1 0.0630; 10.2 0.0316; 10.6 0.0844; 10.10 0.1379; 11.2 −0.1044; 11.9 0.0058 |

In rule-1 form: under resample restore-clean (node, unfrozen) on
ioi/`p_ABC`, n = 2,000, seed 0, no BOS, restoring the clean outputs of 9.6,
9.9 and 10.0 at END together recovers 1.229 of the clean-minus-corrupt gap
(mean `ld` 4.475 against a clean 3.651); restoring 10.7 and 11.10 at END
recovers −0.669 (mean `ld` moves to −2.339, away from clean); restoring the
S-Inhibition heads at END recovers 0.160; restoring the Induction, Duplicate
Token or Previous Token class at its position recovers between −0.027 and
0.001. The verdict is `measured`. These are sufficiency readings on this
prompt pair; they are not evidence about what ablating the same heads does,
which P1–P3 measure.

## O-012

- **5.5.** At weight level, 5.5's K-composition with 4.11 and 2.2 is above the
  random baseline (by 0.0611 and 0.0339; ranks 1 and 6 of 60 earlier heads),
  and so is its Q-composition (by 0.0068 and 0.0153; ranks 15 and 5); at path
  level on IOI, patching 4.11 or 2.2 into the keys of 5.5 and 6.9 at S1+1
  lowers mean `ld` beyond the bound (0.4794 and 0.1263; sign verdicts
  `matched`), while patching them into the queries at S2 does not (0.0004 and
  0.0115; null verdicts `matched`), so the two levels agree on the K-route and
  disagree on the Q-route, where the weights show above-baseline composition
  that the IOI path patch does not register.
- **6.9.** At weight level, 6.9's K-composition with 4.11 and 2.2 is above the
  random baseline (by 0.0674 and 0.0349; ranks 1 and 6 of 72 earlier heads),
  and so is its Q-composition (by 0.0145 and 0.0137; ranks 4 and 7); at path
  level, the same joint runs show the K-route effect and no Q-route effect
  above the bound, so the levels agree on the K-route and disagree on the
  Q-route in the same way as for 5.5 — with the limit that the path runs
  patch 5.5 and 6.9 together as receivers and cannot separate the two heads.

## What this does and does not show

- **Necessity and sufficiency are separate here.** I3, P2 and P3 are
  ablations (necessity readings: what changes when components are removed or
  replaced); I4 and P4 are restore-clean (sufficiency readings: how much of
  the gap writing clean activations in brings back). P1 and I2's path level
  are path patching in the ablate-clean direction. No sentence above carries
  a result from one direction to the other.
- **Identity is by our ranking, not Wang's selection procedure.** Every P1
  `matched` means the published members rank inside k under "ranking by
  path-patching effect"; Wang et al. selected classes from path-patching
  figures plus follow-up tests. I1 ranks by our averaging of Wang's scores on
  our stimulus (BOS, exclusions and averaging were ours to fix).
- **`matched` on a published null** (the I2 Q-route) shows only that we also
  found nothing above the bound; it does not show the route is absent.
- **`bracketed, uninformative`** — none occurred. Had it, it would say that
  the settings the source leaves open span the contrast value, not that the
  claim fails.
- **P2 is `not matched`** at Wang's value over all four pre-registered
  corners. Under the ungated resample sibling the quantity is 0.0544 and
  0.0552, above the published 0.05; the gated verdict is at mean, Wang's
  stated value. That disagreement between ablation values is reported, not
  resolved. The artifacts do not say why, and this README does not offer a
  reason.
- **P3's `matched` rests on the ≈ 7-per-template corners**, which break
  D-014's floor of 30; the two corners that meet the floor alone would not
  contain 0.87.
- **D-006 siblings disagree in places**, and those disagreements are reported,
  not resolved: under zero, 0.1 and 2.2 fall outside their P1 k, the 2.2
  K-route sits just under the floor, and the P2 knockout raises mean `ld`.
  I4 and P4 ran with clean activations only (no siblings).
- **I3 has no published GPT-2 small number.** Olsson et al.'s directional
  expectation comes from other models; under frozen zero ablation the sign
  here is opposite to it for all five units, and under frozen mean and
  resample it is still opposite for 6.9 and 2.2 (and for 4.11 under mean).
  That is a measurement on this battery item and prompt construction, not a
  test of Olsson et al.'s claim. It has been varied only in ablation value
  and pattern freezing: the induction battery has one corruption scheme and
  one prompt construction, so rule 7's template and scheme checks are not
  done (proposals in §I3).
- **Composition scores are weight statistics.** Above-baseline composition
  says the matrices overlap more than random ones of the same shape; it does
  not show that the model uses the route on any task. The path-level check
  is on IOI only, with 5.5 and 6.9 as joint receivers. The pre-named
  question tests Q-composition with 4.11 and 2.2 only, not with any other
  head that could supply a positional signal (O-012 mechanism 2).
- **The noise floor** (F_ioi, and the induction floor used in O-011) was
  measured under node mean ablation on 24 components, none of them the heads
  here; it is used as the pre-registered bound, not as a floor measured for
  these heads or for path patching.
- Backup Name Mover identity, greedy completeness and minimality, Wang's copy
  score, App. A, the adversarial set and Olsson's ICL score are out of E2
  (spec, Boundaries).

## Files and rerun commands

All runs: GPT-2 small at HF revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`
(`607a30d7`), TransformerLens 3.9.0, torch 2.14.0+cu130, RTX 5060,
deterministic algorithms on (each artifact's `environment`). Battery seed 0,
n = 2,000; mean references seed 0 on the corrupt side, template-matched;
I1 stimulus seed 0 (ungated seeds 1–4); I2 baseline 200 draws, seed 0.
Source unchanged between the gate commit `52dcb87` and the last run; each
artifact's `environment.repo_commit` is the branch head when it was written.
I2 was rerun at `84e9af6`, after `composition.json` gained its `environment`
block; every number in its artifacts is bitwise equal to the earlier run.

| Target | Command | Artifacts |
|---|---|---|
| I1 | `uv run python -m src.lesion.e2_reproduce --target I1` | `I1/scores.json`, `I1/verdict.json` |
| I2 | `uv run python -m src.lesion.e2_reproduce --target I2` | `I2/composition.{json,parquet}`, `I2/path/` (12 runs), `I2/verdict.json` |
| I3 | `uv run python -m src.lesion.e2_reproduce --target I3` | 30 runs (5 units × 3 values × frozen/unfrozen), `I3/verdict.json` |
| I4 | `uv run python -m src.lesion.e2_reproduce --target I4` | 5 runs, `I4/verdict.json` |
| P1 | `uv run python -m src.lesion.e2_reproduce --target P1` (`--resume` skips finished (sweep, value) files) | `P1/sweep-{logits,nm_queries,sinh_values,ind_keys}-{zero,mean,resample}.json`, `P1/verdict.json` |
| P2 | `uv run python -m src.lesion.e2_reproduce --target P2` | `P2/{t15-ref210,t15-ref2000,t7-ref98,t7-ref2000,t15-siblings,t7-siblings}/`, `P2/verdict.json` |
| P3 | `uv run python -m src.lesion.e2_reproduce --target P3` | `P3/{t15-ref210,t15-ref2000,t7-ref98,t7-ref2000,t15-siblings,t7-siblings}/`, `P3/verdict.json` |
| P4 | `uv run python -m src.lesion.e2_reproduce --target P4` | `P4/classes/` (7), `P4/heads/` (26), `P4/verdict.json` |
| Exit table | `uv run python -m src.lesion.e2_reproduce --target table` | `verdicts.json` |
| Gates | `uv run pytest -q -m slow tests/test_e2_gates.py` | — |

`--target all` runs I1 to P4 in order. Every artifact carries a top-level
`pre_registered`; a run at any other n or seed writes `null` verdicts. Paths
are relative to `results/E2/`. P1 took about 2 h 8 min on the RTX 5060; the
other targets minutes each.

Artifact shapes under `results/E2/` (key on `phase` and on the presence of
`spec` or `rows`):

- **Run records**: the E1a shape plus `pre_registered`, one JSON and one
  per-prompt parquet per run. Set runs carry `spec.set` and have no
  `spec.component`, `positions`, `receiver` or `mlp_convention`.
- **P1 sweep records**: `config` and `rows` (per-sender aggregates), no
  `spec` and no parquet. In `sweep-*-mean.json`, `reference.hook` names only
  the last sender's `hook_z`; the per-template counts are identical across
  senders.
- **Bespoke records**: `I1/scores.json` and `I2/composition.json`.

PyTorch caching-allocator OOM-retry warnings appeared in some run logs. The
runs completed with all expected artifacts, and the P1 `ind_keys` sweep and
the I2 K-route runs, written in separate processes, agree bitwise on the
senders they share (4.11 and 2.2, effect and sem, under all three values),
which is direct evidence that the numbers are unaffected.
