"""E1b noise floor: how much a mean-ablation cell moves when only the
reference draw changes.

    uv run python -m src.lesion.e1b_noise --item ioi

Per item, default scheme, seed 0, n = 2,000 (every admitted survivor for
factual recall): node mean ablation at all positions, ablate-clean, no
pattern freezing, reference over the corrupt side, template-matched, n =
1,000 (factual: min(1,000, survivors), logged), for each of the 12 MLP layers
and head 0 of each layer, under reference seeds 0-4. Reported per component:
the sample standard deviation of effect_mean across reference seeds, the
per-prompt sem of the seed-0 run, and the larger of the two (the floor a
heatmap cell has to clear). The components and the 5 seeds are ours: this
samples the floor, it does not map it.

Refuses an item whose default-scheme gate artifact did not pass. Writes one
summary JSON per item to results/E1b/noise/{item}/floor.json; no per-run
artifacts."""

from __future__ import annotations

import argparse
import json
import shlex
import statistics
import sys
import time
from pathlib import Path

from src.lesion.ablate import BATTERIES, make_battery, parse_bool
from src.lesion.spec import MLP, AblationSpec, All, Component, Head, MeanReference

COMPONENTS: tuple[Component, ...] = tuple([MLP(layer) for layer in range(12)] + [Head(layer, 0) for layer in range(12)])
REF_SEEDS = (0, 1, 2, 3, 4)
REF_N = 1000
DEFAULT_N = 2000


def noise_spec(component: Component, ref_n: int, ref_seed: int) -> AblationSpec:
    return AblationSpec(component=component, value="mean", reference=MeanReference("corrupt", ref_n, ref_seed, "template"),
                        component_type="node", receiver=None, mlp_convention=None, positions=All(),
                        direction="ablate-clean", freeze_patterns=False)


def summarise(label: str, effects: dict[int, float], sem0: float) -> dict:
    sd = statistics.stdev(effects.values())
    return {"component": label, "effect_mean_by_ref_seed": {str(k): v for k, v in effects.items()},
            "ref_seed_sd": sd, "sem_seed0": sem0, "floor": max(sd, sem0),
            "floor_source": "ref_seed_sd" if sd >= sem0 else "sem"}


def measure_floor(model, battery, components, ref_seeds, n: int, seed: int, ref_n: int, prepend_bos: bool,
                  batch_size: int) -> list[dict]:
    from src.lesion.runner import run

    rows = []
    for component in components:
        effects, sem0 = {}, None
        for rs in ref_seeds:
            spec = noise_spec(component, ref_n, rs)
            eff = run(model, spec, battery, n, seed, prepend_bos, batch_size).aggregates["effect"]["ld"]
            effects[rs] = eff["effect_mean"]
            if rs == ref_seeds[0]:
                sem0 = eff["sem"]
            print(f"  {spec.component_label():7} ref seed {rs}: effect {eff['effect_mean']:+.4f} ± {eff['sem']:.4f}",
                  flush=True)
        rows.append(summarise(noise_spec(component, ref_n, 0).component_label(), effects, sem0))
    return rows


def require_gate_pass(path: Path) -> None:
    """Refuse unless the gate artifact at ``path`` recorded a passing verdict.

    The gate CLI (Task 7) only writes a verdict for a run at the
    pre-registered n and seed; otherwise ``verdict`` is null and the artifact
    carries ``"pre_registered": false``. That case is not a failed gate, it is
    an absent one, so it gets its own message rather than a TypeError from
    indexing into None."""
    path = Path(path)
    if not path.exists():
        raise ValueError(f"{path} missing: run `uv run python -m src.lesion.e1b_gate` first")
    record = json.loads(path.read_text())
    verdict = record["verdict"]
    if verdict is None:
        raise ValueError(f"{path}: no pre-registered verdict; run "
                          "`uv run python -m src.lesion.e1b_gate` at the pre-registered n and seed first")
    if not verdict["pass"]:
        raise ValueError(f"{path}: the item did not pass its gate; no noise floor is measured for it")


def sizes(n_admitted: int | None, n: int | None, ref_n: int) -> tuple[int, int]:
    """(sample n, reference n). Factual recall defaults to every admitted
    survivor and clamps the reference to the survivor count."""
    if n is None:
        n = DEFAULT_N if n_admitted is None else n_admitted
    return n, ref_n if n_admitted is None else min(ref_n, n_admitted)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e1b_noise", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", required=True, choices=sorted(BATTERIES))
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ref-n", type=int, default=REF_N)
    ap.add_argument("--prepend-bos", default=None, help="true|false (default: the battery's own)")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--gate-dir", default="results/E1b/gate")
    ap.add_argument("--out-dir", default="results/E1b/noise")
    args = ap.parse_args(argv)
    cls = BATTERIES[args.item]
    try:
        require_gate_pass(Path(args.gate_dir) / args.item / f"{cls.schemes[0]}.json")
        prepend_bos = cls.default_prepend_bos if args.prepend_bos is None else parse_bool(args.prepend_bos)
    except ValueError as e:
        ap.error(str(e))  # exits 2

    from src.lesion import artifact
    from src.lesion.e1b_gate import battery_record
    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(args.seed)
    model = load_model(args.device)
    battery = make_battery(args.item, plain_tokenizer(), None)
    n, ref_n = sizes(getattr(battery, "n_admitted", None), args.n, args.ref_n)
    t0 = time.time()
    rows = measure_floor(model, battery, COMPONENTS, REF_SEEDS, n, args.seed, ref_n, prepend_bos, args.batch_size)
    record = {
        "phase": "E1b",
        "command": "uv run python -m src.lesion.e1b_noise " + " ".join(shlex.quote(a) for a in argv),
        "item": args.item, "scheme": cls.schemes[0], "n": n, "seed": args.seed, "ref_n": ref_n,
        "ref_seeds": list(REF_SEEDS),
        "spec_template": noise_spec(COMPONENTS[0], ref_n, 0).to_json(),
        "battery": battery_record(battery, n, args.seed, prepend_bos),
        "rows": rows,
        "max_floor": max(r["floor"] for r in rows),
        "environment": artifact.environment_record(model, args.batch_size, time.time() - t0),
    }
    out = Path(args.out_dir) / args.item
    out.mkdir(parents=True, exist_ok=True)
    (out / "floor.json").write_text(json.dumps(record, indent=2))
    print(f"{args.item}: max floor {record['max_floor']:.4f} over {len(rows)} components -> {out / 'floor.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
