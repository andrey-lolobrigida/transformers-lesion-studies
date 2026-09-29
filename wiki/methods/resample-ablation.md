---
title: Resample ablation
type: method
status: drafted
sources: [miller-2024]
first-needed: E1
updated: 2026-09-19
---

# Resample ablation

## In one sentence

Replace a component's activation with its activation on **a different
input** — usually a paired corrupt prompt — so the model stays near its
usual activation distribution while the information that differs between
the two inputs is removed.

## Claim-licence block

| | |
|---|---|
| **Answers** | Necessity of what *differs between the clean input and the specific corrupt input used*. Like [[mean-ablation]] it deletes "information that varies across the distribution, while preserving information that is constant across it" [miller-2024 §3.1.3]. |
| **Does NOT answer** | Necessity of information the corrupt input shares with the clean one (e.g. positional encoding in the Tracr example). Sufficiency, unless run in the restore direction. |
| **Confounds** | The corrupt input **adds signal**, not only removes it: on Sports Players the corrupt prompt always names a different sport, so a resample-ablated model scores 0% where chance is 33% [miller-2024 App. D.2]. Systematically lower IOI faithfulness than mean ablation under node ablation [miller-2024 §4.1]. The pairing rule between clean and corrupt prompts is part of the method. |
| **Always log** | The corrupt distribution and pairing rule; direction; whether one corrupt sample or several per clean prompt; positions; and the rest of the six-tuple on [[ablation-methodology]]. |

## Why it exists

Zero and Gaussian-noise ablation "can take the model significantly out of
distribution … producing noisy outputs". Resample and mean ablation are the
"two more principled approaches" because they "keep the model closer to its
usual distribution of activations" [miller-2024 §3.1.3]. Resample is also
what most of the literature means by *activation patching*: the paper uses
the two terms interchangeably and lists causal tracing and interchange
intervention as other names [miller-2024 §3.1, App. F].

The page exists because D-006 names resample as the third substitution
value E3 sweeps, and because the R0/R1 sources so far had only *used* it
(Wang et al.'s path patching is edge resample ablation in Miller's terms)
without defining it.

## Intuition, then mechanism

**The analogy:** swapping a witness's statement for a different witness's
statement about a different event, rather than for silence (zero) or for
the average of all statements ever made (mean). The court still hears
something statement-shaped.

**Where it breaks.** The other witness's statement is about *some* event.
If every corrupt prompt is built to have a different answer, the swapped-in
activation actively argues for that other answer. That is the Sports
Players effect, and it is why resample and mean can disagree "dramatically"
on an accuracy metric while both being "principled" [miller-2024 App. D.2].

**Mechanism.** For an activation $a$ and a paired corrupt input $x'$, set
$\tilde a = a(x')$ in $F(x) = M(x \mid \operatorname{do}(a = \tilde a))$ [miller-2024 §3.1, eq. 1]. The
paired corrupt prompt keeps the template and changes the task-critical
token — for IOI, the ABC distribution [miller-2024 §4]. Whether the model
runs on the clean input with corrupt values patched in (ablate clean) or on
the corrupt input with clean values patched in (restore clean) is axis 5 of
the six-tuple and changes what the result means; see
[[activation-patching]].

## Precisely

Results in the paper where resample is one arm:

| Circuit | Comparison | Result | Where |
|---|---|---|---|
| IOI (GPT-2 small) | resample vs mean, node ablation, complement, specific positions | resample systematically lower; p = 1e−5 | §4.1, Fig. 3 |
| IOI | same, edge ablation | difference not significant | §4.1 |
| Docstring (4L attn-only) | edge resample vs edge mean | mean "significantly better" | App. D.1, Fig. 9 |
| Sports Players (Pythia 2.8B) | resample vs mean, accuracy | resample 0% (ablated model and circuit), mean ≈ 33% ≈ chance | App. D.2, Fig. 10 |
| Tracr X-Proportion | resample vs zero as ground-truth definition | positional edge unnecessary under resample, necessary under zero | §5, App. D.3 |

Values other than the Sports Players percentages are read off figures.

## What it licenses

"Under resample ablation from {corrupt distribution, pairing rule} of
{component set} at {positions}, {direction}, {metric} changes by {amount}."
The Tracr example is the licence's boundary: a resample result is silent
about anything the clean and corrupt inputs share.

## Where it's contested

- **Is resample "activation patching"?** Miller et al. say yes and treat
  the distinction as connotation — patching edits, ablation deletes
  [miller-2024 §3.1]. This wiki keeps [[activation-patching]] as the page
  for the *procedure and its direction* and this page for the *value*;
  the two overlap by design.
- **Lower faithfulness than mean is not "worse".** The paper's reading is
  that they measure different tasks, not that one is noisier. On Sports
  Players the 0% is the metric correctly reporting that the corrupt signal
  is present.
- **Corrupt prompt design is unexamined here.** The paper takes each
  circuit's original corrupt distribution as given. O-003 is the project's
  version of the question.

## What this project does with it

- **E3's third map** (D-006). The corrupt distribution per battery item is
  the E1 corruption scheme; the pairing rule is logged.
- **E2**: Wang et al.'s path patching is resample at the edge level from
  ABC; the IOI reproduction is already a resample-ablation experiment
  whether or not it is labelled one.
- **Expected direction** (O-009 addendum): a resample-ablated control task
  whose corrupt prompts always carry a competing answer will read *below*
  chance, legitimately. Declare it.

## Sources

- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 3.1 · 3.1.3 · 4 · 4.1 (Fig. 3) · 5 · App. D.1 (Fig. 9) ·
  App. D.2 (Fig. 10) · App. D.3 · App. F.

## Open questions

- One corrupt sample per clean prompt, or an average over several? The
  paper does not say which it used for IOI; the choice sits between
  resample and mean and should be a logged E1 parameter.
