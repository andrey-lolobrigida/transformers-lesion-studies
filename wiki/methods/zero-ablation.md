---
title: Zero ablation
type: method
status: drafted
sources: [wang-2022, miller-2024]
first-needed: E1
updated: 2026-09-19
---

# Zero ablation

## In one sentence

Knock a component out by setting its output to zero — removing both the
information it carried and its average contribution to the residual stream.

## Claim-licence block

| | |
|---|---|
| **Answers** | Necessity of the component's *entire* output, average included. |
| **Does NOT answer** | Sufficiency. Nor, on its own, whether an observed drop is due to lost information or to downstream components losing an implicit bias they relied on. |
| **Confounds** | Off-distribution state: zero is a value the component never emits. Wang et al.: "subsequent nodes might rely on the average activation value as an implicit bias term" [wang-2022 §2.1]. |
| **Always log** | Which components, positions, metric, seed, model revision hash. |

## Why it exists, and what question it asks

Wang et al. reject it in a sentence: "a first naïve knockout approach
consists of simply deleting each node in `K` from `M`. The net effect of
this removal is to zero ablate `K` … we find zero ablation to lead to noisy
results in practice" [wang-2022 §2.1]. No comparison is shown. Miller et
al. agree that "the zero point is arbitrary" and that zero and
Gaussian-noise ablation "can take the model significantly out of
distribution" [miller-2024 §3.1.3], and then say what zero ablation is
*for* rather than only what is wrong with it.

**The question it asks, per Miller et al.** Mean and resample delete only
what varies across their reference distribution; zero deletes everything
the component carries, including what is constant. So the two define
different tasks. In the compiled Tracr X-Proportion model, one edge
carries only positional encoding — constant across inputs — and "if we
instead use Zero Ablations, then this information will be destroyed, so
the edge must be included in the circuit" [miller-2024 §5]. For IOI: "Do
you want your IOI circuit to include the mechanism that decides it needs
to output a name? Then use zero ablations" [miller-2024 §6].

That is D-006's position, sourced: zero is not the crude version of mean;
it asks the broader question. `docs/01-methods.md` already says so in its
own words.

## Where it's contested

- Off-distribution, by everyone's account. What that costs in a model with
  LayerNorm — residual-norm distortion — is the R2 material (Rushing &
  Nanda, per O-008), not here.
- Wang et al.'s "noisy" is unquantified; Miller et al. do not run zero
  ablation on the language-model circuits at all ("we focus on Mean and
  Resample Ablations" [miller-2024 §3.1.3]). The only zero-ablation
  measurement in either source is the Tracr one.

## What this project does with it

E3's first map (D-006). The result doc says, per rule 3, which task the
zero map is measuring — the one that includes deciding the output type —
and does not call disagreement with the mean map noise.

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 2.1.
- [miller-2024] Miller, Chughtai & Saunders, arXiv 2407.08734v1.
  Sections cited: 3.1.3 · 5 · 6.
