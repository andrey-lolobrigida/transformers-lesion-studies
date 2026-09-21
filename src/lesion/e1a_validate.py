"""E1a slow tier: runs the validation CLI commands and prints the MLP table.

    uv run python -m src.lesion.e1a_validate               # everything
    uv run python -m src.lesion.e1a_validate --only identity
    uv run python -m src.lesion.e1a_validate --only mlp
    uv run python -m src.lesion.e1a_validate --only frozen   # exploratory, not an exit check
    uv run python -m src.lesion.e1a_validate --only rerun    # determinism twin of the MLP0 call, into rerun/
    uv run python -m src.lesion.e1a_validate --only table    # print the 12 x 3 table from the artifacts

Every artifact is a CLI run with its exact command recorded; this script only
sequences them. Sizes (n=2000, reference n=1000 over p_ABC, seed 0) are this
phase's choice, logged in the artifacts; Wang et al. state neither.
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
            "--out-dir", OUT]


def mlp_args(layer: int, freeze: bool, out_dir: str = OUT) -> list[str]:
    return ["--component", f"L{layer}.mlp", "--value", "all", *REF, "--freeze" if freeze else "--no-freeze",
            "--n", N_TABLE, "--batch-size", "256", "--out-dir", out_dir]


def ablate(args: list[str]) -> None:
    cmd = [sys.executable, "-m", "src.lesion.ablate", *COMMON, *args]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def table(freeze: bool) -> str:
    suffix = "_frozen" if freeze else ""
    rows = ["| MLP layer | zero: effect ± sem | mean (p_ABC, n=1000): effect ± sem | resample (p_ABC): effect ± sem | mean-ablated mean ld (sign) |",
            "|---|---|---|---|---|"]
    for layer in range(12):
        cells = []
        signed = ""
        for value in ("zero", "mean-corrupt-n1000-s0-template", "resample"):
            path = Path(OUT) / f"ioi_L{layer}mlp_{value}_node_all_ablate-clean{suffix}_n{N_TABLE}_seed0.json"
            if not path.exists():
                cells.append("missing")
                continue
            d = json.loads(path.read_text())
            eff = d["results"]["effect"]["ld"]
            cells.append(f"{eff['effect_mean']:+.3f} ± {eff['sem']:.3f}")
            if value.startswith("mean"):
                m = d["results"]["ablated"]["mean_ld"]
                signed = f"{m:+.3f} ({'negative' if m < 0 else 'positive'})"
        rows.append(f"| {layer} | " + " | ".join(cells) + f" | {signed} |")
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=["identity", "mlp", "frozen", "rerun", "table"], nargs="*", default=None)
    only = set(ap.parse_args().only or ["identity", "mlp", "frozen", "rerun", "table"])
    if "identity" in only:
        ablate(IDENTITY)
    if "mlp" in only:
        for layer in range(12):
            ablate(mlp_args(layer, freeze=False))
    if "frozen" in only:
        for layer in range(12):
            ablate(mlp_args(layer, freeze=True))
    if "rerun" in only:
        # The determinism twin has to be the *same* command, not a command that
        # produces the same artifact: a --value mean call records a different
        # cli.value and a different command string from the --value all call
        # that wrote the table's MLP0 artifacts, and the check is that two
        # invocations differ only in environment.seconds. So: layer 0 again,
        # byte for byte, into a second output directory.
        ablate(mlp_args(0, freeze=False, out_dir=f"{OUT}/rerun"))
    if "table" in only:
        print("\nUnfrozen (exit check 2):\n" + table(False))
        print("\nPattern-frozen (exploratory):\n" + table(True))


if __name__ == "__main__":
    main()
