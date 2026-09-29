---
title: Self-repair (backup heads, compensation after ablation)
type: phenomenon
status: drafted
sources: [wang-2022]
first-needed: E4
updated: 2026-09-19
---

# Self-repair

*Opened at the first source that reports the phenomenon. Rushing & Nanda
2024, McGrath et al. 2023 and Conditional Co-Ablation (R2) are where the
mechanism, the LayerNorm share and the current state of the E4 gap live.
Until R2 this page records the original observation only.*

## In one sentence

After a set of heads is knocked out, other heads change their contribution
so that the metric drops far less than the knocked-out heads' contribution
would predict — in Wang et al., removing the three Name Movers costs about
5% of the logit difference, and eight previously minor heads become the
main direct contributors.

## Why it exists

Wang et al. did not go looking for it. Having found the Name Movers, they
knocked all three out at once as a completeness check: "To our surprise, the
circuit still worked (only 5% drop in logit difference)" [wang-2022 §3.4].
Re-running the direct-effect [[path-patching]] experiment after the knockout
showed new heads at the top of the ranking — "these new heads compensate for
the loss of Name Movers Heads by replacing their role."

For this project it is the spine (D-002). This page holds the observation
that the spine is built on, in the form its source gave it.

## Intuition, then mechanism

**The analogy:** understudies. Remove the lead and the understudy performs;
you would not have known the understudy could, watching the show with the
lead in place.

**Where it breaks.** An understudy is idle until needed. Wang et al.'s
Backup Name Movers are *not* idle: they have small but non-zero effects
intact (the smallest minimality scores in the circuit, down to about 1% of
$F(M)$ against $K$ = the other name-moving heads [wang-2022 App. K]), and several are doing
something else — attending equally to IO and S, or preferring S1, or
tracking clause subjects [wang-2022 §App. F]. And "compensation" is a
description of the logits, not of a mechanism: the paper says explicitly
that "both the reason and the mechanism of this compensation effect are
still unclear" [wang-2022 §App. F].

**What was measured** [wang-2022 §3.4, App. F, Fig. 15]:

- Knockout of Name Movers 9.6, 9.9, 10.0 by [[mean-ablation]] on `p_ABC`:
  logit difference about 5% lower.
- After the knockout, the direct-effect ranking changes. The Negative Name
  Movers become *less* negative, and 10.7 turns positive. Heads that had
  slightly positive effects before "become the main contributors".
- Eight of them, not already in any class and with effect above 2%, are
  named Backup Name Movers: 9.0, 10.1, 10.10, 10.6 (Name-Mover-like
  pre-knockout); 10.2, 11.9 (attend equally to S1 and IO, write both); 11.2
  (attends more to S1, writes toward $W_U[\mathrm{S}]$); 9.7 (attends to S2, writes
  negatively) [wang-2022 App. F, Fig. 16].
- Among heads that turn positive after the knockout are also the
  S-Inhibition heads [wang-2022 App. F].

**The authors' hypothesis:** dropout. "We hypothesize that this compensation
phenomenon is caused by the use of dropout during training. Thus, the model
was optimized for robustness to dysfunctional parts. More work is needed to
determine the origin of this phenomenon and if such compensation effects can
be observed beyond our special case" [wang-2022 §3.4].

**One-line checkpoint:** knock out the copying heads, the copy still
happens, and the heads now doing it were not idle before — they were doing
something slightly different.

## Precisely

The measured object is the difference between two direct-effect rankings
(intact vs post-knockout), and one scalar: the knockout drop. No
decomposition into causes is attempted in this source. The LayerNorm
rescaling account that D-002 names as the "mechanical" share is *not* in
Wang et al.; the nearest thing in the sources read so far is Olsson et al.'s
caveat that "to the extent two heads do something similar and the layer norm
before the logits rescales things, the importance of individual heads may be
masked" [olsson-2022 §Argument 3, via [[pattern-preserving-ablation]]].

## What it licenses

The observation licenses: "under mean ablation on `p_ABC`, knocking out
{9.6, 9.9, 10.0} at END changes mean logit difference by ≈ 5%, and the
direct-effect ranking under path patching changes as listed." It licenses a
*necessity* statement about the Name Movers that is surprisingly weak, and a
statement that other heads' direct effects *changed*.

It does not license "backup heads are learned redundancy" — the dropout
hypothesis is offered as a hypothesis — nor any split between mechanical and
compensatory shares. The glossary's distinction between mechanical and
compensatory self-repair is this project's framing, to be sourced at R2.

## Where it's contested

- **Cause unknown, by the authors' statement.** Dropout is a conjecture.
- **Whether it generalises** beyond IOI in GPT-2 small is explicitly left
  open [wang-2022 §3.4]. R2's sources are where the generality is tested.
- **The knockout method conditions the size.** 5% is a mean-ablation figure;
  what zero ablation would give is not reported. O-008 notes that Rushing &
  Nanda compare the two.
- **What counts as a backup is a threshold** (2%) and a search (direct effect
  after one particular knockout). A different knockout would name a
  different set — that is the point the completeness criterion makes
  formally [[circuit-validation-criteria]].

## What this project does with it

- **E4's originating observation.** The published number to reproduce first
  is the 5% drop under the stated conditions; the published *set* is the
  eight heads above. O-008 asks how much of E4 is reproduction; this page
  says what the 2022 baseline is.
- **E3's heatmaps understate heads like these by construction**: a
  single-head ablation of 10.10 in the intact model gives its small intact
  effect. The direct-effect-vs-total-effect gap (O-011 resolution) is the
  E3-native signal that something is being masked; identifying *which* heads
  step up is E4's sub-question 3, and O-007 says MLPs must be ablatable for
  that answer to be complete.
- **Provenance for the E4 writeup**: the phenomenon was found in a
  completeness check, named as a limitation of circuit discovery, and
  attributed to dropout as a conjecture. The sober register CLAUDE.md
  requires is the register of the source.

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 1 · 3.4 · 4.1 · App. F (Figs. 15, 16) · App. K.
- [olsson-2022] Olsson et al., 2022, §Argument 3 — the masking caveat, cited
  via [[pattern-preserving-ablation]].

## Open questions

- Is the dropout hypothesis testable on this project's hardware? It would
  need a model trained without dropout at comparable scale; Pythia (O-004)
  was trained without dropout [unverified — check the Pythia paper before
  relying on this]. If true, the E6 model choice doubles as a test.
- Which of the eight Backup heads step up under *zero* and *resample*
  ablation of the Name Movers? Cheap at E4; unreported here.
