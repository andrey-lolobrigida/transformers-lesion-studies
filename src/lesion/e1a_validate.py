"""E1a slow tier: runs the validation CLI commands and prints the MLP table.

    uv run python -m src.lesion.e1a_validate               # everything
    uv run python -m src.lesion.e1a_validate --only identity
    uv run python -m src.lesion.e1a_validate --only mlp
    uv run python -m src.lesion.e1a_validate --only frozen   # exploratory, not an exit check
    uv run python -m src.lesion.e1a_validate --only rerun    # determinism twin of the MLP0 mean call, into rerun/
    uv run python -m src.lesion.e1a_validate --only table    # print the 12 x 3 table from the artifacts

Every artifact is a CLI run with its exact command recorded; this script only
sequences them, one CLI call per (layer, value). Sizes (n=2000, reference
n=1000 over p_ABC, seed 0) are this phase's choice, logged in the artifacts;
Wang et al. state neither.

Artifacts are grouped under results/E1a/ by check and value:
identity/, mlp/{zero,mean,resample}/, mlp_frozen/{zero,mean,resample}/, rerun/.
``artifact_path`` is the single place that layout is spelled out.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

OUT = "results/E1a"
N_TABLE = "2000"
REF = ["--ref-side", "corrupt", "--ref-n", "1000", "--ref-seed", "0", "--ref-match", "template"]
COMMON = ["--battery", "ioi", "--type", "node", "--positions", "all", "--direction", "ablate-clean",
          "--seed", "0", "--prepend-bos", "false"]

IDENTITY = ["--component", "L0H0", "--value", "zero", "--no-freeze", "--n", "100000", "--batch-size", "512",
            "--out-dir", f"{OUT}/identity"]

VALUES = ("zero", "mean", "resample")


def value_stem(value: str) -> str:
    """The fragment ``stem()`` (src/lesion/artifact.py) writes for a value; only
    "mean" expands, since it carries the reference spec in the filename."""
    return "mean-corrupt-n1000-s0-template" if value == "mean" else value


def artifact_path(check: str, value: str | None = None, layer: int | None = None, frozen: bool = False) -> Path:
    """The only place the grouped layout is spelled out. Returns the JSON path;
    the parquet twin is the same path with its suffix swapped."""
    if check == "identity":
        return Path(OUT) / "identity" / "ioi_L0H0_zero_node_all_ablate-clean_n100000_seed0.json"
    if check == "rerun":
        name = f"ioi_L0mlp_{value_stem(value)}_node_all_ablate-clean_n{N_TABLE}_seed0.json"
        return Path(OUT) / "rerun" / name
    if check == "mlp":
        sub = "mlp_frozen" if frozen else "mlp"
        suffix = "_frozen" if frozen else ""
        name = f"ioi_L{layer}mlp_{value_stem(value)}_node_all_ablate-clean{suffix}_n{N_TABLE}_seed0.json"
        return Path(OUT) / sub / value / name
    raise ValueError(f"unknown check: {check!r}")


def mlp_args(layer: int, value: str, freeze: bool, out_dir: str) -> list[str]:
    args = ["--component", f"L{layer}.mlp", "--value", value]
    if value == "mean":
        args += REF
    args += ["--freeze" if freeze else "--no-freeze", "--n", N_TABLE, "--batch-size", "256", "--out-dir", out_dir]
    return args


def ablate(args: list[str]) -> None:
    cmd = [sys.executable, "-m", "src.lesion.ablate", *COMMON, *args]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def table(freeze: bool) -> str:
    rows = ["| MLP layer | zero: effect ± sem | mean (p_ABC, n=1000): effect ± sem | resample (p_ABC): effect ± sem | mean-ablated mean ld (sign) |",
            "|---|---|---|---|---|"]
    for layer in range(12):
        cells = []
        signed = ""
        for value in VALUES:
            path = artifact_path("mlp", value, layer, freeze)
            if not path.exists():
                raise FileNotFoundError(str(path))
            d = json.loads(path.read_text())
            eff = d["results"]["effect"]["ld"]
            cells.append(f"{eff['effect_mean']:+.3f} ± {eff['sem']:.3f}")
            if value == "mean":
                m = d["results"]["ablated"]["mean_ld"]
                signed = f"{m:+.3f} ({'negative' if m < 0 else 'positive'})"
        rows.append(f"| {layer} | " + " | ".join(cells) + f" | {signed} |")
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=["identity", "mlp", "frozen", "rerun", "table"], nargs="+", default=None)
    only = set(ap.parse_args().only or ["identity", "mlp", "frozen", "rerun", "table"])
    if "identity" in only:
        ablate(IDENTITY)
    if "mlp" in only:
        for layer in range(12):
            for value in VALUES:
                ablate(mlp_args(layer, value, freeze=False, out_dir=f"{OUT}/mlp/{value}"))
    if "frozen" in only:
        for layer in range(12):
            for value in VALUES:
                ablate(mlp_args(layer, value, freeze=True, out_dir=f"{OUT}/mlp_frozen/{value}"))
    if "rerun" in only:
        # The determinism twin has to be the *same* command, not a command that
        # produces the same artifact: the check is that two invocations differ
        # only in environment.seconds (and the out-dir). So: the mlp/mean/
        # layer-0 command again, byte for byte, into a second output directory.
        ablate(mlp_args(0, "mean", freeze=False, out_dir=f"{OUT}/rerun"))
    if "table" in only:
        print("\nUnfrozen (exit check 2):\n" + table(False))
        print("\nPattern-frozen (exploratory):\n" + table(True))


if __name__ == "__main__":
    main()
