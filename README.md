# Lesion Studies for Transformers

Disabling parts of a small language model on purpose, and measuring carefully
what breaks.

The method is borrowed from neuroscience: damage a component, observe the
deficit, infer the function. Transformers make a better subject than brains in
some respects — the intervention is exact, repeatable, and reversible — and a
worse one in others, since ablation pushes the model into internal states no
input could produce, and every downstream component sees the disturbance.

## What's here

This is a **reproduction-first** project. The plan is to replicate known
results carefully, then map where they stop holding: under different ablation
methods, different prompt distributions, different models. Boundary-mapping is
the goal; anything novel is expected to emerge from it rather than be hunted
directly.

The intended spine is self-repair after ablation, with the mechanical component
controlled for — separating the part of a model's post-lesion recovery that is
a side effect of layer normalisation from the part that is actual compensation.
That is a lean, not a commitment; it is decided after E3.

Primary subject: GPT-2 small. Every result is stated under a named ablation
method on a named dataset, zero-, mean- and resample-ablation are reported side
by side, and every number carries a rerun command, a seed and a model revision
hash. The rules are in [`CLAUDE.md`](CLAUDE.md#epistemic-rules).

## Status

Reading phases R0–R1 and experiment phases E0–E3 are done; each is a branch
(`phase-…`) and a tag (`v-…`). Next is the E4 spine decision and reading phase
R2. Each phase's results directory has a `README.md` that states what was
measured, what it licenses, and the command for every number.

| Phase | Tag | What it produced | Results |
|---|---|---|---|
| E0 | `v-E0` | Environment and smoke test; the published IOI baseline is bracketed, not matched (D-011) | [`results/E0/`](results/E0/README.md) |
| E1a | `v-E1a` | Ablation harness, validated on IOI: bitwise identity against E0, determinism, and the MLP0 bracket against Wang et al. App. J under all three substitution values | [`results/E1a/`](results/E1a/README.md) |
| E1b | `v-E1b` | Task battery: IOI, induction and subject–verb agreement pass their gates; factual recall fails (64 admitted CounterFact survivors against the 300 required) and is logged as a negative result | [`results/E1b/`](results/E1b/README.md) |
| E2 | `v-E2` | Reproduction of 21 published entries, pre-registered (`4675ba6`): 16 matched, 4 measured, 1 not matched (the Name Mover knockout) | [`results/E2/`](results/E2/README.md) |
| E3 | `v-E3` | Functional map over the battery, pre-registered (`96591d2`), with held-out replication and adversarial checks | [`results/E3/`](results/E3/README.md) |

Corrections made after a phase closed are in [`ERRATA.md`](ERRATA.md).

## Reproducing

Needs Python 3.12+, [uv](https://docs.astral.sh/uv/) and a CUDA GPU (developed
on an 8 GB RTX 5060); setup notes and known gotchas are in
[`docs/06-environment.md`](docs/06-environment.md). The model is pinned by
Hugging Face revision and downloaded on first run.

```
uv sync
uv run python -m src.lesion.e0_smoke --n 100000 --seed 0   # E0
uv run pytest -q -m "not slow"                              # fast tests, no GPU
```

The commands for E1a–E3 are listed in each phase's results README. The committed artifacts under `results/` are the record; rerunning
reproduces them.

## Licence and third-party data

Code and documents are MIT ([`LICENSE`](LICENSE)). One exception:
`batteries/factual/survivors.json` contains records from CounterFact
(Meng et al. 2022), downloaded from
`https://rome.baulab.info/data/dsets/counterfact.json`, with the source
SHA-256 recorded in the file. No licence for the dataset itself has been
published (the ROME code repository is MIT; checked 2026-10-11), so those
records are not covered by this repository's licence. The factual-recall item
failed its gate in E1b and is not used in E2 or E3.

## Documents

| File | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Operating manual: epistemic rules, conventions, what not to do |
| [`docs/00-motivation.md`](docs/00-motivation.md) | Why this project; where the neuroscience framing breaks |
| [`docs/01-methods.md`](docs/01-methods.md) | The methods, and what each measurement licenses |
| [`docs/02-roadmap.md`](docs/02-roadmap.md) | Reading phases R0–R3, experiment phases E0–E6 |
| [`docs/03-reading-list.md`](docs/03-reading-list.md) | Papers, grouped by the phase that needs them |
| [`docs/04-decisions.md`](docs/04-decisions.md) | Dated decision log, open questions, null results |
| [`docs/05-glossary.md`](docs/05-glossary.md) | Terms |
| [`docs/06-environment.md`](docs/06-environment.md) | Hardware, install order, gotcha log |
| [`docs/07-alignment-extension.md`](docs/07-alignment-extension.md) | A parked successor project, for after the core plan ships |
| [`wiki/`](wiki/README.md) | Concept pages extracted from the papers; a reading scaffold, not a source of results |

## How this was built

A single author, working with Claude (Anthropic) as a coding and research
assistant. `CLAUDE.md` is the instruction file Claude works under, and it is
kept in the repo because it is also the project's statement of method.
Decisions are the author's and are logged in `docs/04-decisions.md`.

## Scope

The minimum complete version is reading phases R0–R1 plus experiment phases
E0–E4 on GPT-2 small: a verified reproduction, a functional map produced under
three ablation methods, and one careful extension. Anything past that gets
planned when reached.
