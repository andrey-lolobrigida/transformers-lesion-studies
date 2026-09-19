---
title: Zero ablation
type: method
status: stub
sources: [wang-2022]
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

## Status

Stub. The only source read so far that discusses it does so to reject it:
"a first naïve knockout approach consists of simply deleting each node in `K`
from `M`. The net effect of this removal is to zero ablate `K` … we find zero
ablation to lead to noisy results in practice" [wang-2022 §2.1]. No
comparison is shown. See [[mean-ablation]] for the alternative the paper
adopts and for why the reference distribution matters.

D-006 disagrees with the framing rather than the observation: zero and mean
ask different questions, and E3 runs both. `docs/01-methods.md` makes the
same point. Miller et al. (R1) and Rushing & Nanda (R2, residual-norm
distortion under zero ablation, per O-008) are the sources that will turn
this stub into a page.

## Sources

- [wang-2022] Wang et al., "Interpretability in the Wild", arXiv 2211.00593v1.
  Sections cited: 2.1.
