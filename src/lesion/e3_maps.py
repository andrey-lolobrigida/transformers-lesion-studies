"""E3 figures, generated from results/E3/selection/tests.json and the E1b
gate artifacts only.

    uv run python -m src.lesion.e3_maps     # -> results/E3/figures/{item}_{group}_{raw|scaled}.png (18 files)

Per item, three groups, each drawn together and never one alone: the six
total-effect maps (row 1 unfrozen, row 2 frozen; columns zero, mean,
resample), the three direct-effect maps, the three frozen deltas. Each in raw
logits and scaled by the item's clean-minus-corrupt gap (E1b gate, seed 0).
A panel is a 12 x 12 head grid (layer down, head across) with the 12 MLP
layers as a column at its right. Diverging colour: blue where the
intervention raised the mean ld, red where it lowered it, neutral gray at 0.
One symmetric scale per figure, set by the largest |head cell| in it, so its
panels compare; an MLP cell beyond that scale is drawn at the end colour and
printed with its value. A dot marks a cell that clears Holm over the main
family; an x marks an exact-zero delta (untested)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from src.lesion.e3_prereg import ALPHA, COMPONENTS, DIRECT_MAPS, ITEM, N, N_FAMILY, SEED, TOTAL_MAPS, VALUES, label
from src.lesion.spec import Head

NEG, MID, POS = "#2a78d6", "#f0efec", "#e34948"  # diverging pair with a neutral midpoint
INK, SURFACE = "#333333", "#fcfcfb"
GROUPS = {"total": [[m.id for m in TOTAL_MAPS[:3]], [m.id for m in TOTAL_MAPS[3:]]],
          "direct": [[m.id for m in DIRECT_MAPS]],
          "delta": [[f"delta_{v}" for v in VALUES]]}
GROUP_TITLES = {"total": "total effect (node, all positions, ablate-clean)",
                "direct": "direct effect (edge to logits, wang convention, unfrozen)",
                "delta": "frozen delta (frozen effect minus unfrozen effect)"}


def panel_title(map_id: str) -> str:
    parts = map_id.split("_")
    if parts[0] == "total":
        return f"{parts[1]}, {parts[2]}"
    if parts[0] == "direct":
        return parts[1]
    return f"{parts[1]}: frozen minus unfrozen"


def panel(tests_by_key: dict, item: str, map_id: str) -> dict:
    p = {"heads": np.full((12, 12), np.nan), "mlp": np.full(12, np.nan),
         "reject_heads": np.zeros((12, 12), bool), "reject_mlp": np.zeros(12, bool),
         "exact_heads": np.zeros((12, 12), bool), "exact_mlp": np.zeros(12, bool)}
    for c in COMPONENTS:
        t = tests_by_key[(item, map_id, label(c))]
        kind, idx = ("heads", (c.layer, c.head)) if isinstance(c, Head) else ("mlp", c.layer)
        p[kind][idx] = t["effect"]
        p[f"reject_{kind}"][idx] = t["reject"]
        p[f"exact_{kind}"][idx] = not t["tested"]
    return p


def scale_limit(panels: list[dict], div: float) -> float:
    m = max(float(np.nanmax(np.abs(p["heads"]))) for p in panels) / div
    return m if m > 0 else 1.0


def clipped(p: dict, vmax: float, div: float) -> list[int]:
    return [l for l in range(12) if abs(p["mlp"][l] / div) > vmax]


def _draw(item: str, group: str, panels: dict, div: float, scale_label: str, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("e3_diverging", [NEG, MID, POS]).with_extremes(bad=SURFACE)
    rows = GROUPS[group]
    vmax = scale_limit(list(panels.values()), div)
    fig, axes = plt.subplots(len(rows), 3, figsize=(13, 3.9 * len(rows) + 0.7), squeeze=False, facecolor=SURFACE,
                             constrained_layout=True)
    im = None
    for r, row in enumerate(rows):
        for col, map_id in enumerate(row):
            ax, p = axes[r][col], panels[map_id]
            grid, rej, exact = np.full((12, 14), np.nan), np.zeros((12, 14), bool), np.zeros((12, 14), bool)
            grid[:, :12], grid[:, 13] = p["heads"] / div, p["mlp"] / div
            rej[:, :12], rej[:, 13] = p["reject_heads"], p["reject_mlp"]
            exact[:, :12], exact[:, 13] = p["exact_heads"], p["exact_mlp"]
            ax.set_facecolor(SURFACE)
            im = ax.imshow(grid, cmap=cmap, vmin=-vmax, vmax=vmax, interpolation="nearest")
            ys, xs = np.nonzero(rej)
            ax.scatter(xs, ys, s=6, c=INK, marker="o", linewidths=0)
            ys, xs = np.nonzero(exact)
            ax.scatter(xs, ys, s=10, c=INK, marker="x", linewidths=0.6)
            for l in clipped(p, vmax, div):
                v = p["mlp"][l] / div
                ax.text(13, l, f"{v:+.0f}" if abs(v) >= 10 else f"{v:+.1f}", ha="center", va="center", fontsize=4.5,
                        color="white")
            ax.set_xticks([0, 2, 4, 6, 8, 10, 13], ["0", "2", "4", "6", "8", "10", "MLP"])
            ax.set_yticks(range(12))
            ax.tick_params(labelsize=7, colors=INK, length=0)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_xlabel("head", fontsize=8, color=INK)
            ax.set_ylabel("layer", fontsize=8, color=INK)
            ax.set_title(panel_title(map_id), fontsize=9, color=INK)
    cb = fig.colorbar(im, ax=axes, shrink=0.75)
    cb.set_label(scale_label, fontsize=8, color=INK)
    cb.ax.tick_params(labelsize=7)
    fig.suptitle(f"{item}: {GROUP_TITLES[group]}; n = {N:,}, seed {SEED}. Dot: clears Holm "
                 f"(alpha = {ALPHA}, {N_FAMILY:,} tests). x: exact zero, untested.", fontsize=9, color=INK)
    fig.savefig(out_path, dpi=150, facecolor=SURFACE, metadata={"Software": None})
    plt.close(fig)


def render(tests: list[dict], gaps: dict[str, float], out_dir, items=None) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_key = {(t["item"], t["map"], t["component"]): t for t in tests}
    paths = []
    for item in items or tuple(ITEM):
        for group, rows in GROUPS.items():
            panels = {map_id: panel(by_key, item, map_id) for row in rows for map_id in row}
            for scale in ("raw", "scaled"):
                div = 1.0 if scale == "raw" else gaps[item]
                scale_label = ("effect on the mean logit difference (logits)" if scale == "raw"
                               else f"effect / clean-minus-corrupt gap ({gaps[item]:.3f})")
                path = out_dir / f"{item}_{group}_{scale}.png"
                _draw(item, group, panels, div, scale_label, path)
                paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e3_maps", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-root", default="results/E3")
    args = ap.parse_args(argv)
    root = Path(args.out_root)
    tests = json.loads((root / "selection" / "tests.json").read_text())["tests"]
    gaps = {i: json.loads(Path(ITEM[i].gate_file).read_text())["statistics"]["gap"] for i in ITEM}
    for p in render(tests, gaps, root / "figures"):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
