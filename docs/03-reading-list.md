# 03 — Reading list

Organised by the phase that needs it, not by topic. Anything not attached to a
phase is deferred — this list is a queue, not a survey.

arXiv IDs are given where confirmed. Items marked `[unverified]` need checking
before being cited in a writeup.

---

## R0 — Orientation

- **Olah et al., 2020 — "Zoom In: An Introduction to Circuits" (Distill).**
  Where circuit-thinking comes from. Vision models, but the framing is the
  point.
- **Elhage et al., 2021 — "A Mathematical Framework for Transformer Circuits"
  (Anthropic).** QK/OV decomposition; how to reason about a head as a thing
  rather than a blob. Dense. Read the QK/OV sections properly even if the rest
  gets skimmed.
- **Olsson et al., 2022 — "In-context Learning and Induction Heads"
  (Anthropic).** The circuit E2 reproduces, and the argument for why it might
  underlie in-context learning.

---

## R1 — Methods and epistemics

- **Wang et al., 2022 — "Interpretability in the Wild: a Circuit for Indirect
  Object Identification in GPT-2 small."** The canonical ablation + patching
  case study, and the original source of the backup-head observation. Read
  closely; E1's battery and E2's reproduction both lean on it.
- **Miller, Chughtai & Saunders, 2024 — "Transformer Circuit Faithfulness
  Metrics are not Robust" (arXiv 2407.08734).** The paper that reframes the
  whole methods section. Faithfulness scores are highly sensitive to ablation
  methodology; the ablation determines the task. Their `auto-circuit` library
  is also a practical starting point for the harness.
- Meng et al., 2022 — "Locating and Editing Factual Associations in GPT"
  (ROME). Causal tracing applied to factual knowledge; the source of E1's
  factual-recall battery design.
- Chan et al., 2022 — "Causal Scrubbing" (Redwood, Alignment Forum). Skim for
  the shape of the rigour endgame; full engagement only if the project gets
  there.
- Makelov, Lange & Nanda — "Is This the Subspace You Are Looking For? An
  Interpretability Illusion for Subspace Activation Patching." Read if the
  project ever patches directions rather than whole components.

---

## R2 — Self-repair (gates E4)

- **Rushing & Nanda, 2024 — "Explorations of Self-Repair in Language Models"
  (arXiv 2402.15390, ICML 2024).** The core paper for E4. LayerNorm rescaling
  as a mechanical driver of apparent self-repair; self-repair as imperfect and
  noisy; an unexplained residual. Code at `starship006/backup_research`.
- **McGrath et al., 2023 — "The Hydra Effect: Emergent Self-repair in Language
  Model Computations" (arXiv 2307.15771).** Ablate one attention layer, a later
  one takes over. The phenomenon at layer granularity.
- **"Conditional Co-Ablation: Recovering Self-Repair Backups in Transformer
  Circuits" (arXiv 2607.01940).** Recent — roughly July 2026. Validated on the
  GPT-2 IOI backup heads with transfer to induction across multiple
  architectures. Read before committing to E4; it may have closed part of the
  gap. `[verify venue and author list before citing]`

---

## R3 — Field map (optional)

- **"Open Problems in Mechanistic Interpretability," 2025 (arXiv 2501.16496).**
  Multi-author field map. Read to find where the field thinks the gaps are.
- Tigges, Hanna, Yu & Biderman, 2024 — "LLM circuit analyses are consistent
  across training and scale" (arXiv 2407.10827). Direct prior work for E6.
- Mueller et al., 2025 — "Mechanistic Interpretability Benchmark (MIB)."
  Standardised circuit-localisation evaluation. Relevant only if a venue
  decision makes comparability matter.

---

## Deferred — the feature/SAE direction

Not part of the current plan. Listed so the decision to defer is visible rather
than accidental. See `docs/04-decisions.md` D-003.

- Elhage et al., 2022 — "Toy Models of Superposition" (Anthropic). Why single
  neurons are polysemantic.
- Bricken et al., 2023 — "Towards Monosemanticity"; Templeton et al., 2024 —
  "Scaling Monosemanticity" (Anthropic). Sparse autoencoders as the response.
- Gemma Scope 2 (DeepMind, Dec 2025) — SAEs and transcoders on every layer of
  Gemma 3, 270M through 27B. If the project ever goes feature-level on a modern
  model, this is the substrate. Browsable via Neuronpedia without training
  anything.

---

## Tooling documentation (read before E0, not papers)

- **TransformerLens** tutorials — the primary tool. Hooks on every activation.
- **ARENA** interpretability curriculum — the best hands-on ramp; can run in
  parallel with R0/R1 as practice, but does not substitute for the papers.
- **`auto-circuit`** (Miller et al.) — efficient implementations of many
  ablation methodologies. Likely saves real time in E1.
- **nnsight / NDIF** docs — only if TransformerLens becomes a ceiling.
  `remote=True` for large hosted models is the escape hatch if a question ever
  needs scale.
- **SAELens / Neuronpedia** — deferred with the SAE direction.
