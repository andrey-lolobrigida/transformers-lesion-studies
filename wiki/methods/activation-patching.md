---
title: Activation patching
type: method
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E2
updated: 2026-09-19
---

# Activation patching

*Drafted from Wang et al., where it is a secondary technique, and Miller et
al., who supply the direction taxonomy. Meng et al. (ROME, causal tracing)
is the R1 skim that would add a worked restore-direction example; Makelov
et al. the subspace illusion.*

## In one sentence

Replace the **output** of a set of components with their output on a
different input, then recompute the **whole** forward pass from there and
measure the metric — the coarse relative of [[path-patching]], with nothing
frozen.

## Claim-licence block

| | |
|---|---|
| **Answers** | Depends on the *direction*. Patching a corrupted activation into a clean run (Wang et al.'s use) asks necessity: "does the clean output depend on what these components carried?" Patching a clean activation into a corrupted run asks sufficiency: "is restoring these components enough to restore the behaviour?" The two are not the same experiment, and the page for the second is not yet written from a source. |
| **Does NOT answer** | Anything about *which route* the effect took: every downstream component responds, including other heads. That is the trade against [[path-patching]], and it is a trade — coarser about routes, but able to see within-class interactions that path patching holds fixed. |
| **Confounds** | The counterfactual input defines what information is replaced; Wang et al. build six of them to separate two signals and the decomposition is only as clean as the datasets. Downstream compensation (backup heads) is *included* in the number, since nothing is frozen. Patched components at one position only — alignment across templates must hold. |
| **Always log** | The set of patched components and positions, the counterfactual distribution(s) and how they were constructed, direction (which run receives the patch), number of samples, metric, seed, model revision hash. |

## Why it exists

Wang et al. introduce it as the tool for a question path patching cannot ask.
Path patching freezes every non-sender head, so it cannot see effects that
depend on several heads of the same class interacting — and Section 3.4 had
just shown that the Backup Name Movers and Negative Name Movers *do* depend
on the earlier heads of their class. So, "instead of patching isolated paths,
we patch the output of a set of heads and recompute the forward pass of the
model after this modification" [wang-2022 §App. A].

The page exists because the roadmap (E2, E3) and `docs/01-methods.md` lean on
"activation patching" as the sufficiency test, and the first source read that
actually performs it performs it in the *other* direction. Getting the
direction wrong is the necessity/sufficiency confusion of epistemic rule 2 in
its most literal form.

## Intuition, then mechanism

**The analogy:** a transplant rather than a plumbing test. Take the S-Inhibition
heads' output from a sentence where the names were arranged differently, graft
it into the current sentence, and let the rest of the model do whatever it
does with the graft.

**Where it breaks.** A transplant is one organ; here the graft is a *set* of
heads at one position, and everything downstream — other heads included —
readjusts. The number you read at the logits is the total response, backups
and all. That is what makes it the right tool for "what do these heads carry?"
and the wrong tool for "by which route does it matter?"

**Mechanism, as used in the paper** [wang-2022 §App. A]:

1. Build a counterfactual distribution by transforming `p_IOI`. Three
   transformations are used, and composed, to give six datasets:
   - *Random name flip*: replace names by random names, positions kept, each
     name consistently. Only the **position** signal survives; token signal is
     uncorrelated.
   - *IO ↔ S1 flip*: swap the positions of IO and S1. Token signal correct,
     **position** signal inverted.
   - *IO ← S2 replacement*: make IO the subject and S the indirect object.
     Both signals inverted.
2. Run the model on the counterfactual; cache the S-Inhibition heads' outputs.
3. Run on the original `p_IOI` sample with those outputs written in; recompute
   everything downstream; read logit difference.

The result decomposes additively. With `S_pos ∈ {1, −1}` for original versus
inverted position signal and `S_tok ∈ {1, 0, −1}` for original, uncorrelated,
inverted token signal, the patched logit difference is approximated by
`2.31 S_pos + 0.99 S_tok`, with mean error 7% relative to the baseline
[wang-2022 §App. A, Fig. 9]:

| | Original position | Inverted position |
|---|---|---|
| Original token | 3.55 (baseline) | −0.99 |
| Random token | 2.45 | −1.96 |
| Inverted token | 1.77 | −3.16 |

With both signals inverted the Name Movers "attend and copy the S1 token
instead of the IO token" [wang-2022 §App. A, Fig. 10]. The same patching from
sentences with longer prefixes but the same S1–S2 distance leaves the logit
difference unchanged (3.56 → 3.57), which the authors read as the position
signal being *relative*, not absolute.

The same technique is used once more to locate the position signal upstream:
patching the outputs of the Induction and Duplicate Token heads from
altered-position sentences reproduces at least 88% of the drop obtained by
patching the S-Inhibition heads, while patching from same-position,
different-name sentences gives less than 8% of it [wang-2022 §3.3].

**The direction taxonomy, from Miller et al.** — added 2026-09-19. In their
frame activation patching *is* [[resample-ablation]] ("we consider
activation patching to be a specific type of ablation, and use the term
Resample Ablation interchangeably"), also called causal tracing or
interchange intervention [miller-2024 §3.1, App. F]. Node patching with a
cached activation is "vanilla activation patching" [miller-2024 §3.1.2].
What this page calls the direction problem is axis 5 of the
[[ablation-methodology]] six-tuple, crossed with axis 6:

| Input | Direction | Set | Faithfulness target |
|---|---|---|---|
| Clean | ablate clean | circuit | destroy performance |
| Corrupt | restore clean | circuit | restore performance |
| Clean | ablate clean | complement | maintain performance |
| Corrupt | restore clean | complement | maintain inefficacy |

[miller-2024 §3.1.5, Table 3]. Wang et al.'s Appendix A experiments are row
1 with "circuit" = the S-Inhibition heads. `docs/01-methods.md`'s
"activation patching tests sufficiency" is row 2. The two "maintain" rows
are not equivalent: restoring clean values into the circuit on a corrupt
input lets clean signal "flow through edges not included in the circuit"
[miller-2024 §3.1.5, Fig. 2].

## What it licenses

- Wang et al.'s use (corrupted → clean) licenses: "under activation patching
  of {components} at {position} from {counterfactual distribution} into
  `p_IOI`, logit difference changes by {amount}." **Necessity of the
  information those components carried**, with the counterfactual defining
  what "the information" is.
- The additive decomposition licenses a claim about *what* is carried — two
  separable signals — because the datasets were designed so each transformation
  moves exactly one of them. That is a design property, not a property of the
  method.
- The restore direction (clean → corrupted) is the one `docs/01-methods.md`
  describes and the one epistemic rule 2 calls a sufficiency test. Its
  definition is now sourced (Table 3, row 2); a worked example is not, and
  ROME is the skim that would supply one.

## Where it's contested

- **The direction problem, stated once.** "Activation patching tests
  sufficiency" (glossary, methods doc) is true of one direction and false of
  the other. The first paper on this project's list to perform it performs
  the necessity direction. Miller et al. make direction an explicit axis and
  list both in the prior literature (Vig, ROME, Docstring restore; Wang,
  ACDC, Greater-than, Sports Players ablate) [miller-2024 Table 2]. A result
  doc must state which run received the patch.
- **Interpretability illusions** for patching into subspaces (Makelov et al.,
  R1 conditional read) — not yet extracted; recorded so the page has a slot
  for it.
- **Nothing in this source varies the metric or the counterfactual family**
  beyond the six datasets built for one question.

## What this project does with it

- **E2 verifies by patching** (roadmap; D-004). Before that runs, the E2
  results doc has to say whether its patching is denoising (restore clean into
  corrupted) or noising (write corrupted into clean); the two answer different
  halves of rule 2.
- **E1's IOI battery** gets the `p_ABC` corruption for ablation and path
  patching, and can get the three Appendix A transformations as *named*
  additional corruption schemes. Whether it should is O-003.
- **E3's "verify with activation patching before naming a head"** (roadmap
  E3 exit criterion) means the denoising direction. This page will cite the
  source for that once one is read.

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 3.3 · App. A (Figs. 9, 10).
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 3.1 · 3.1.2 · 3.1.5 (Table 3, Fig. 2) · Table 2 · App. F.

## Open questions

- ~~What is the sufficiency-direction reference?~~ Defined by Miller et
  al.'s Table 3 (2026-09-19); a worked example still wants ROME.
- Should the E1 battery record, per corruption scheme, *which signals it
  removes* in the style of Wang et al.'s six-dataset design? It would make
  O-003's answer measurable rather than argued.
