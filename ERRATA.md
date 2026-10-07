# Errata

Corrections to documents from earlier phases, fixed forward and recorded here
(policy: `CLAUDE.md`, "Working conventions"). Newest first. Old phase
branches are not rewritten.

## 2026-10-07 — direct effect under `wang`; total − direct is a net figure

**Affected:** `docs/01-methods.md`, "Direct effect, this project's sense"
(R1, `b307396`); `docs/02-roadmap.md`, E1 harness paragraph (R0, `3a47df4`).
Every phase from E1a onward reads these sentences.

**Was:**
1. Methods: the direct effect holds "every other path from $a$ to the logits
   … frozen at its clean value, so only $a$'s own contribution to the final
   residual state changes."
2. Methods: "$\Delta_{\mathrm{total}} - \Delta_{\mathrm{direct}}$ is the
   downstream compensation."
3. Roadmap: "the gap between them is the self-repair number E4 starts from."

**Is:**
1. Under the `wang` convention (the harness default; E2 and E3 use it) only
   other attention heads' outputs are held. Later MLPs and the final
   LayerNorm recompute, so their response to $a$ is inside the direct
   effect. The decision log already stated this correctly (O-011, "Resolution of the R1 trigger",
   2026-09-19, item 1: "`wang`: MLPs recompute on the direct path"); the code
   (`interventions.run_edge`) does the same.
2. and 3. Total − direct is the net effect of routes through later heads.
   It contains the component's own indirect effect as well as any
   compensation, and it misses compensation by later MLPs or the final
   LayerNorm under `wang`. It stays E4's baseline, read as a net figure.

**Numbers affected:** none. No artifact, test or selection changes. The
correction is about what the direct effect and the gap measure, not about
any value.

**Found:** E3 map walk, 2026-10-07. Reading D, F and U side by side,
L9H9 (IOI, mean) gives D +2.51, F +2.58, U +0.26, and L8.mlp gives D −0.005,
F +0.035, U −0.385. That made it necessary to check what D actually
includes.

**Fixed in:** `b318591` (methods) and the commit that adds this file
(roadmap), both on `phase-E3-functional-map`. They reach `main` when E3
fast-forwards. The policy says fix on `main`; the branch was the author's
call, so the fix travels with the phase that found it.

**Not changed, flagged for E4's design:** O-007 (`docs/04-decisions.md`)
expects E4 to find compensation in MLPs. Under `wang`, D − U cannot see
it; `term` may be the convention E4 needs.
