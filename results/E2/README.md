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
