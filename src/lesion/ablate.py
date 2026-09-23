"""CLI for one ablation run (E1a). Every axis is a required flag except the
convenience defaults listed under ``build_parser``; all of them, typed or
not, are written into the artifact.

Example (the MLP0 check, mean value):

    uv run python -m src.lesion.ablate \
      --battery ioi --component L0.mlp \
      --value mean --ref-side corrupt --ref-n 1000 --ref-seed 0 --ref-match template \
      --type node --positions all --direction ablate-clean --no-freeze \
      --n 2000 --seed 0 --prepend-bos false --batch-size 256 --out-dir results/E1a

``--value all`` runs zero, mean and resample in sequence and writes three
artifacts. ``--type edge`` needs ``--receiver logits|inputs`` and
``--mlp-convention wang|term``; ``--receiver inputs`` takes ``--target
L9H9.q@END`` repeated. Ill-formed requests exit 2 before the model loads.

``--corruption`` picks the battery's corruption scheme (default: its first,
the gated one); ``--prepend-bos`` defaults per battery. Both are written to
the artifact as resolved.
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path

from src.lesion.battery import resolve_scheme
from src.lesion.induction import InductionBattery
from src.lesion.ioi import IOIBattery
from src.lesion.spec import (
    MLP, AblationSpec, All, Component, Head, Indices, Inputs, Labels, Logits, MeanReference, Positions, SpecError,
)

# name -> battery class. Class attributes (labels, schemes, default_prepend_bos)
# are read before the model loads; instances are built after, by make_battery.
BATTERIES = {"ioi": IOIBattery, "induction": InductionBattery}


def make_battery(name: str, tokenizer, scheme: str | None):
    return BATTERIES[name](tokenizer, scheme)


def resolve_battery_defaults(args: argparse.Namespace) -> None:
    """Fill the per-battery defaults in place, so the artifact's ``cli`` block
    records the value used whether it was typed or not. Raises ValueError on an
    unknown scheme or a battery whose data is missing, before any model loads."""
    cls = BATTERIES[args.battery]
    preflight = getattr(cls, "preflight", None)
    if preflight is not None:
        preflight()
    args.corruption = resolve_scheme(cls.schemes, args.corruption)
    if args.prepend_bos is None:
        args.prepend_bos = "true" if cls.default_prepend_bos else "false"


def parse_component(s: str) -> Component:
    if m := re.fullmatch(r"L(\d+)H(\d+)", s):
        return Head(int(m.group(1)), int(m.group(2)))
    if m := re.fullmatch(r"L(\d+)\.mlp", s):
        return MLP(int(m.group(1)))
    raise ValueError(f"component must look like L9H9 or L0.mlp, got {s!r}")


def parse_positions(s: str) -> Positions:
    if s == "all":
        return All()
    if s.startswith("idx:"):
        body = s[len("idx:"):]
        if not body:
            raise ValueError("idx: needs at least one index")
        return Indices(tuple(int(x) for x in body.split(",")))
    labels = tuple(x for x in s.split(",") if x)
    if not labels:
        raise ValueError("positions needs 'all', labels like END,S2, or idx:3,7")
    return Labels(labels)


def parse_target(s: str) -> tuple[int, int, str, str]:
    if m := re.fullmatch(r"L(\d+)H(\d+)\.([qkv])@(\S+)", s):
        return int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
    raise ValueError(f"target must look like L9H9.q@END, got {s!r}")


def parse_bool(s: str) -> bool:
    if s.lower() in ("true", "1", "yes"):
        return True
    if s.lower() in ("false", "0", "no"):
        return False
    raise ValueError(f"expected true or false, got {s!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m src.lesion.ablate", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--battery", required=True, choices=sorted(BATTERIES))
    ap.add_argument("--corruption", default=None,
                    help="corruption scheme (default: the battery's first, e.g. p_ABC for ioi)")
    ap.add_argument("--component", required=True, help="L{layer}H{head} or L{layer}.mlp")
    ap.add_argument("--value", required=True, choices=["zero", "mean", "resample", "all"])
    ap.add_argument("--ref-side", choices=["clean", "corrupt"], help="mean: which side the mean is over")
    ap.add_argument("--ref-n", type=int, help="mean: reference draw size")
    ap.add_argument("--ref-seed", type=int, help="mean: reference draw seed")
    ap.add_argument("--ref-match", choices=["template", "pooled"], help="mean: per-template or one pooled vector")
    ap.add_argument("--type", required=True, choices=["node", "edge"], dest="component_type")
    ap.add_argument("--receiver", choices=["logits", "inputs"], help="edge: what receives the substitution")
    ap.add_argument("--target", action="append", default=[], help="edge --receiver inputs: L9H9.q@END, repeatable")
    ap.add_argument("--mlp-convention", choices=["wang", "term"], help="edge: MLPs recompute (wang) or are held (term)")
    ap.add_argument("--positions", required=True, help="'all', labels like END,S2, or idx:3,7")
    ap.add_argument("--direction", required=True, choices=["ablate-clean", "restore-clean"])
    ap.add_argument("--freeze", action=argparse.BooleanOptionalAction, required=True,
                    help="--freeze or --no-freeze: pin every attention pattern to the destination run")
    # Convenience defaults. Each is written to the artifact whether typed or not.
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--prepend-bos", default=None,
                    help="true|false (default: the battery's own; false for ioi and factual, true for induction)")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", default="results/E1a")
    return ap


def specs_from_args(args: argparse.Namespace) -> list[AblationSpec]:
    """One spec per substitution value. Raises SpecError or ValueError on anything ill-formed."""
    component = parse_component(args.component)
    positions = parse_positions(args.positions)
    values = ["zero", "mean", "resample"] if args.value == "all" else [args.value]
    reference = None
    if "mean" in values:
        missing = [f for f in ("ref_side", "ref_n", "ref_seed", "ref_match") if getattr(args, f) is None]
        if missing:
            raise SpecError("--value mean needs " + ", ".join("--" + f.replace("_", "-") for f in missing))
        reference = MeanReference(args.ref_side, args.ref_n, args.ref_seed, args.ref_match)
    receiver = None
    if args.component_type == "edge":
        if args.receiver == "logits":
            receiver = Logits()
        elif args.receiver == "inputs":
            receiver = Inputs(tuple(parse_target(t) for t in args.target))
    elif args.receiver is not None or args.target:
        raise SpecError("--receiver and --target are edge-only flags")
    labels = BATTERIES[args.battery].labels
    if isinstance(positions, Labels):
        for label in positions.labels:
            if label not in labels:
                raise SpecError(f"unknown position label {label!r}; {args.battery} has {labels}")
    if isinstance(receiver, Inputs):
        for _, _, _, label in receiver.targets:
            if label not in labels:
                raise SpecError(f"unknown position label {label!r}; {args.battery} has {labels}")
    if args.prepend_bos is not None:
        parse_bool(args.prepend_bos)
    return [
        AblationSpec(component=component, value=v, reference=reference if v == "mean" else None,
                     component_type=args.component_type, receiver=receiver, mlp_convention=args.mlp_convention,
                     positions=positions, direction=args.direction, freeze_patterns=args.freeze)
        for v in values
    ]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        resolve_battery_defaults(args)
        specs = specs_from_args(args)
    except (SpecError, ValueError) as e:
        ap.error(str(e))  # exits 2

    # Nothing above touched the model. Heavy imports from here on.
    from src.lesion import artifact
    from src.lesion.model import load_model, plain_tokenizer, set_determinism
    from src.lesion.runner import run

    prepend_bos = parse_bool(args.prepend_bos)
    set_determinism(args.seed)
    model = load_model(args.device)
    battery = make_battery(args.battery, plain_tokenizer(), args.corruption)
    command = "uv run python -m src.lesion.ablate " + " ".join(shlex.quote(a) for a in argv)
    for spec in specs:
        result = run(model, spec, battery, args.n, args.seed, prepend_bos, args.batch_size)
        env = artifact.environment_record(model, args.batch_size, result.seconds)
        record = artifact.build_record(result, spec, battery, command, env, vars(args))
        json_path, _ = artifact.write(record, result, Path(args.out_dir))
        eff = result.aggregates["effect"]["ld"]
        ref = "" if result.reference_summary is None else f"  ref n={result.reference_summary['n']}"
        print(f"{spec.component_label():8} {spec.value:8} {spec.component_type:4} "
              f"clean ld {result.aggregates['clean']['mean_ld']:.4f}  ablated ld {result.aggregates['ablated']['mean_ld']:.4f}  "
              f"effect {eff['effect_mean']:.4f} ± {eff['sem']:.4f}{ref}  [{result.seconds:.1f}s]  -> {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
