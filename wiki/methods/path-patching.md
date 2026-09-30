---
title: Path patching
type: method
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E1
updated: 2026-09-19
---

# Path patching

## In one sentence

Run the model on a clean input, but for **one set of paths** — from a chosen
sender head to a chosen set of receivers, through residual connections and
MLPs but *not* through other heads — substitute the sender's activation from a
different input, and measure how much the metric drops.

## Claim-licence block

| | |
|---|---|
| **Answers** | Necessity of a *route*, not of a component: "does the model's output on the clean input depend on what head $h$ sends to receiver $r$ along the direct path $h \to r$?" With $r$ = the final residual state, this is the head's **direct effect** on the logits. |
| **Does NOT answer** | Sufficiency. The intervention in Wang et al. is *noising* — a corrupted activation is written into a clean run — so a large effect says the clean path was needed, not that it would suffice. It is also silent about every path that passes through another head: those are held at their clean values by construction, so a head whose whole influence is routed through other heads scores zero here and is not thereby shown unimportant. |
| **Confounds** | The corrupted input defines what is removed (Wang et al. use `p_ABC`, which removes name identity and duplication while keeping the template). Other heads are frozen to clean values, which is a state the model never produces. MLPs and LayerNorms *are* recomputed, so the "direct" path includes MLP mediation. Backup behaviour is invisible: freezing the other heads prevents any compensation, which is the point, but means the number is not the one a full ablation would give. |
| **Always log** | The sender, the receiver set (which input — Q, K or V — of which heads, or the residual end state), the pair of distributions $(x_{\text{orig}}, x_{\text{new}})$, the number of pairs averaged (Wang et al.: more than 200), the metric, seed, model revision hash. |

## Why it exists

Ablating a head and watching the logits move tells you the head mattered, but
not *how* its contribution reached the output. Wang et al. wanted the
opposite: to trace the circuit backwards from the logits one edge at a time —
"which heads directly affect the output?", then "which heads affect *those*
heads' queries?", and so on [wang-2022 §3]. That needs an intervention that
distinguishes a head's **direct** effect on a receiver from its **indirect**
effect via other heads. Path patching is that intervention. The authors
describe it as generalising the causal-mediation analysis of Vig et al. 2020
to language models [wang-2022 §3].

The method earns a page because O-011's third path-restriction value, *direct
effect*, is operationally this method with the receiver set to the residual
end state, and because E2's IOI reproduction cannot be run without it.

## Intuition, then mechanism

**The analogy:** a plumbing test. You want to know whether the water reaching
tap $r$ comes through pipe $h \to r$ specifically. So you hold every other
pipe's flow exactly where it was, swap the contents of that one pipe for
coloured water, and look at the tap. If the tap runs coloured, the pipe was
carrying something the tap used.

**Where the analogy breaks, twice.** First, the "coloured water" is not a
tracer but a *corruption*: the sender's activation on an input where the
task cannot be done. So what you see at the tap is a *drop*, and the drop is
a necessity signal, not a flow measurement. Second, "every other pipe held
fixed" is done by freezing other heads' outputs to their clean values — but
MLPs and LayerNorms in between are recomputed, so they *do* respond to the
change. The paths Wang et al. call direct run "through residual connections
and MLPs (but not through other attention heads)" [wang-2022 §3.1]. This is
not the same as "the head's own term in the path expansion"; see *Where it's
contested*.

**Now the mechanism.** Four forward passes [wang-2022 §App. B, Algorithm 1]:

- **A.** Run on $x_{\text{new}}$ (corrupted); cache every activation.
- **B.** Run on $x_{\text{orig}}$ (clean); cache every activation.
- **C.** Run on $x_{\text{orig}}$ with every head *frozen* to its pass-B output,
  except the sender $h$, which is set to its pass-A output. MLPs and
  LayerNorms recompute. Save what the receivers $r \in R$ *would* compute in
  this state (their own value is then overwritten, since they are frozen).
- **D.** Run on $x_{\text{orig}}$ normally, but overwrite each receiver with the value
  saved in C. Everything after the receivers recomputes as in a normal
  forward pass. Read the logits.

The metric (logit difference in every experiment of the paper) is compared
between pass D and the clean model, averaged over more than 200 $(x_{\text{orig}}, x_{\text{new}})$ pairs [wang-2022 §App. B].

"Freezing" is defined in the paper as the special case of patching where a
forward pass on $x$ has some earlier activations edited and an activation is
then patched back to the value it had on the *unedited* run of $x$
[wang-2022 §App. B, fn. 4]. It is freezing of **head outputs**, not of
attention patterns — the distinction from [[pattern-preserving-ablation]] is
exactly this.

**One-line checkpoint:** corrupt one sender, pin every other head to clean,
let the MLPs respond, deliver the result to the receivers only, and read the
drop.

## Precisely

Inputs [wang-2022 §App. B]:

- $x_{\text{orig}}$: a sample from `p_IOI`; $x_{\text{new}}$: the corresponding sample from
  `p_ABC` (names replaced by three unrelated random names, template kept).
- $h$: the sender, a (head, position) pair — in the paper always a single
  head at one named position (END, S2, S1+1).
- $R \subseteq M$: the receivers. Either the Q, K or V input of a set of heads, or
  the residual end state. The end state is what the logits are computed from
  (after the final LayerNorm), so choosing $R$ = end state measures the
  direct effect of $h$ on the logits [wang-2022 §App. B, fn. 3].

In pass C, "all attention heads except $h$ have their output frozen to their
value on $x_{\text{orig}}$. This means that we remove the influence of every path
including one (or more) intermediate attention heads $p$ of the form
$h \to p \to r$" [wang-2022 §App. B]. What remains is every path $h \to r$ whose
only intermediate nodes are residual connections, MLPs and LayerNorms.

The experiments the paper runs with it, receiver by receiver:

| Receiver $R$ | Sender position | Finds | Section |
|---|---|---|---|
| Residual end state (logits) | END | Name Movers 9.6, 9.9, 10.0; Negative Name Movers 10.7, 11.10 | §3.1 |
| Name Movers' queries | END | S-Inhibition 7.3, 7.9, 8.6, 8.10 | §3.2 |
| S-Inhibition values | S2 | Duplicate Token 0.1, 3.0; Induction 5.5, 6.9 | §3.3 |
| S-Inhibition keys | S2 | Duplicate Token reversed; fuzzy heads 5.9, 5.8, 0.10 | App. C |
| S-Inhibition queries | — | "no significant direct effect" | §3.3 |
| Induction Heads' keys | S1+1 | Previous Token 4.11, 2.2 | App. D |
| Induction Heads' queries | S2 | no significant effect | App. D |
| Residual end state, after knocking out the Name Movers | END | Backup Name Movers | §3.4, App. F |
| Residual end state, sender = an MLP layer | — | MLP direct effects | App. J |

Sign convention: a *drop* in logit difference when the path is corrupted
means the path contributes *positively*; the Negative Name Movers produce a
*rise* [wang-2022 §3.1].

## What it licenses

Under epistemic rule 1: "under path patching from `p_ABC` into `p_IOI`, with
receiver $R$, corrupting the path $h \to R$ changes mean logit difference by
{amount} over {N} pairs." Read as a **necessity claim about that route**.

Three things it does not license, all of which the paper itself respects:

- **Not sufficiency.** No clean activation is restored into a corrupted run
  anywhere in the method. The "sufficiency" vocabulary of `docs/01-methods.md`
  applies to the *denoising* direction of [[activation-patching]], which this
  is not.
- **Not a whole-head importance.** A head can matter entirely through paths
  that route via other heads and score nothing here. The paper handles this
  by tracing *backwards*: once the S-Inhibition heads are found via the Name
  Movers' queries, their own senders are found via *their* inputs. The
  indirect effect is recovered edge by edge, never in one number.
- **Not robust to what has already been removed.** Running the same
  $h \to \text{logits}$ experiment after knocking out the Name Movers produces a
  different ranking — that is how the Backup Name Movers were found
  [wang-2022 §3.4]. The paper's own summary: "different model structure is
  found when some components are ablated" [wang-2022 §1]. See [[self-repair]].

## Where it's contested

- **"Direct effect" means something different here than on
  [[path-expansion]].** The O-011 resolution defines direct effect as "only
  the head's own contribution to the logits", and the path-expansion page
  restates it as keeping only the term $A^h \otimes W_U W_{OV}^h (\ldots)$. Wang et al.'s
  direct effect keeps every path from $h$ to the logits that avoids other
  *heads* — MLPs and LayerNorms are recomputed and so mediate the effect
  [wang-2022 §3.1, §App. B]. In an attention-only model the two coincide; in
  GPT-2 small they do not. Which one E1 implements is an unmade decision;
  proposed as an addendum to O-011.
- **In Miller et al.'s taxonomy this is edge resample ablation** — added
  2026-09-19. "Wang et al. (2023) perform a further simplified version of
  path patching … This is equivalent to Edge Resample Ablation in our
  terminology … Importantly, Wang et al. reason that the IOI task should be
  an attention-only task … As such, they take nodes to only be attention
  heads, with MLPs considered to be part of the direct path between nodes"
  [miller-2024 App. F]. That is the direct-effect discrepancy above, named
  from outside: Wang's direct effect is an *edge* in a graph whose nodes are
  heads only. Miller et al. also record that the IOI circuit "is specified
  as an edge-level circuit, but Wang et al. evaluate its faithfulness via a
  node-wise ablation methodology", and that evaluating it at the edge level
  gives a median faithfulness "well over 100%" [miller-2024 §4, §4.1]. See
  [[ablation-methodology]].
- **The paper uses two different "freezings", and neither is Olsson's.**
  Path patching freezes *head outputs* (pass C). [[pattern-preserving-ablation]]
  freezes *attention patterns* and lets outputs respond. A pattern-preserving
  ablation of $h$ lets the ablation reach later heads' values; path patching
  to the logits lets it reach nothing downstream except MLPs. These are three
  distinct points on the path-restriction axis, not two.
- **The corrupted distribution is part of the measurement.** `p_ABC` was
  chosen because mean-ablating on `p_IOI` "would not remove enough information
  helpful for the task" [wang-2022 §2.1]. Every number on this page is
  relative to that choice. Bears on O-003.
- **Within-class interactions are invisible, by the authors' own account.**
  Appendix A switches to [[activation-patching]] precisely because "the
  output of later (Backup) Name Mover Heads and Negative Heads depend on
  earlier heads from these classes, such that it is not possible to ignore the
  interactions between heads inside a class (as it is the case in path
  patching)" [wang-2022 §App. A].
- **The final LayerNorm is a stated approximation.** The head-output
  projections used to *characterise* the found heads (not path patching
  itself) ignore the final LayerNorm's scaling; the authors say approximating
  it "resulted in similar correlation and scatter plots" [wang-2022 §3.1,
  fn. 1].

## What this project does with it

- **E1 implements it as the direct-effect setting** of the path-restriction
  axis, with the definition question above settled first. The four-pass
  structure (A, B, C, D) is the reference implementation; any deviation is a
  recorded choice.
- **E2's IOI reproduction** re-runs the first three rows of the table above:
  $h \to \text{logits}$ at END, $h \to$ Name Mover queries at END, $h \to$ S-Inhibition
  values at S2. Published head identities, and the sign of each, are the
  numbers to check against; see [[ioi-circuit]].
- **E3 records direct effect per head in the same run as total effect**
  (O-011 resolution, decision 2). This page is what "direct effect" cites.
  The gap between the two is E4's starting number, and this page's second
  contested bullet is the reason that gap has to state which freezing it used.
- **Epistemic rule 2 wording.** Path patching in this paper is an ablation of
  a path. Results from it are written in necessity language, with "path"
  named, never as "restoring".

## Sources

- [wang-2022] Wang, Variengien, Conmy, Shlegeris & Steinhardt,
  "Interpretability in the Wild: a Circuit for Indirect Object Identification
  in GPT-2 small", arXiv 2211.00593v1, 1 November 2022.
  https://arxiv.org/abs/2211.00593
  Sections cited: 1 · 2.1 · 3 · 3.1 (incl. fn. 1) · 3.2 · 3.3 · 3.4 ·
  App. A · App. B (incl. fn. 3, fn. 4, Algorithm 1) · App. C · App. D ·
  App. F · App. J.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 4 · 4.1 · App. F.

## Open questions

- **Which "direct effect" does the harness compute** — Wang et al.'s
  (MLPs recompute) or the pure path-expansion term (MLPs held)? Cheap to
  offer both; expensive to discover after E3 that the wrong one was
  recorded. Proposed for O-011.
- **Does path patching with $x_{\text{new}}$ drawn from a different corruption change
  the found circuit?** The paper only ever uses `p_ABC`. Same question as
  O-003, seen from this method.
