# 02 — The "shape of the optimization surface" programme exists

*2026-09-02. A pointer so I don't forget this is a thing. Not on the reading
list, not a plan.*

The intuition from note 01 — that a phase change in training should be
visible in the geometry of the loss surface, not just in behaviour — is the
core of what its authors call **developmental interpretability**. Rough shape,
from memory and **all references `[unverified]`** until I open them:

- **Singular learning theory** as the theoretical backbone. The key quantity
  is the *local learning coefficient*, an estimate of how "flat" or
  degenerate the loss surface is around the current weights. Stage-wise
  changes in it are read as phase transitions in what the model has learned.
- Hoogland et al., "The Developmental Landscape of In-Context Learning"
  `[unverified, arXiv 2402.02364?]` — applies this to a small transformer and
  reports stages that line up with induction-head formation. This is the
  closest thing to what I imagined.
- The "edge of stability" line (Cohen et al.) `[unverified]` tracks the top
  Hessian eigenvalue during training and is the classic "loss-surface
  geometry over time" observable. Different community, same instinct.
- Chen et al., "Sudden drops in the loss" `[unverified, arXiv 2309.07311?]`
  — phase transitions and syntax acquisition in masked LMs. Adjacent.

Why it is *not* in this project: checkpoints give weights, not training
dynamics; the observables are Hessian spectra and learning-coefficient
estimates, not lesions; and it is a live research programme with its own
tooling. It would be a successor project, the way `docs/07` is. Worth one
evening of reading if E6 ever gets planned, to avoid reinventing their figures.
