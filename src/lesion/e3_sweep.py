"""E3 sweep driver (D-016 item 2): every (item, map, component) cell through
``runner.run``, written as one record per cell set.

    uv run python -m src.lesion.e3_sweep --item all --stage selection  # 27 cell sets, 4,212 cells -> results/E3/sweep/
    uv run python -m src.lesion.e3_sweep --item all --stage floor      # ref seeds 1-4 of every mean map, 5,616 -> results/E3/floor/
    uv run python -m src.lesion.e3_sweep --item ioi --stage selection --maps total_zero_unfrozen \
        --components L0H0,L0.mlp --n 64 --out-root scratch/E3        # a smoke run; not pre-registered

A cell set is one (item, map) grid of 156 cells at one (prompt seed,
reference seed). Its JSON holds every cell's spec, aggregates and reference
summary, and the environment. Per-prompt ablated ld and P[c] go to one
long-format parquet only where a later step reads them: the selecting draw at
reference seed 0 here, and the held-out draw (e3_verify writes it through
this module). Clean columns are stored once per (item, prompt seed), and
every cell's clean pass is checked against them bitwise. No battery meta text
is stored: prompts are regenerated from the generator and seed the record names.

Resumable: a cell is skipped when the record already holds it with the same
spec and the same code revision (the last commit touching src/lesion/). A
record written under a different config is refused, never overwritten. Runs
refuse uncommitted changes under src/lesion/ unless --allow-dirty, which never
writes under results/."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.lesion import artifact, e1b_gate, runner
from src.lesion.e3_prereg import (
    BATCH_SIZE, COMPONENTS, ITEM, MAP, MAPS, N, REF_N, REF_SEEDS, SEED, Map, label, parse_label,
)
from src.lesion.spec import AblationSpec, All, Component, Logits, MeanReference, Positions

STAGES = ("selection", "floor")


class SweepError(RuntimeError):
    """The sweep cannot go on without overwriting or mixing records. A hard stop."""


@dataclass(frozen=True)
class CellSet:
    item: str
    map_id: str
    prompt_seed: int
    ref_seed: int | None  # None for zero and resample

    @property
    def stem(self) -> str:
        return f"{self.map_id}_s{self.prompt_seed}" + ("" if self.ref_seed is None else f"_r{self.ref_seed}")


def cell_spec(component: Component, m: Map, ref_seed: int | None, positions: Positions = All(),
              direction: str = "ablate-clean") -> AblationSpec:
    reference = MeanReference("corrupt", REF_N, ref_seed, "template") if m.value == "mean" else None
    if m.kind == "total":
        return AblationSpec(component=component, value=m.value, reference=reference, component_type="node",
                            receiver=None, mlp_convention=None, positions=positions, direction=direction,
                            freeze_patterns=m.frozen)
    return AblationSpec(component=component, value=m.value, reference=reference, component_type="edge",
                        receiver=Logits(), mlp_convention="wang", positions=positions, direction=direction,
                        freeze_patterns=False)


def cell_sets(items: tuple[str, ...], stage: str, maps: tuple[str, ...] | None = None) -> list[CellSet]:
    """``selection``: every map at the selecting draw (reference seed 0 for mean
    maps). ``floor``: reference seeds 1-4 of every mean map."""
    wanted = [m for m in MAPS if maps is None or m.id in maps]
    if stage == "selection":
        return [CellSet(i, m.id, SEED, REF_SEEDS[0] if m.value == "mean" else None) for i in items for m in wanted]
    if stage == "floor":
        return [CellSet(i, m.id, SEED, rs) for i in items for m in wanted if m.value == "mean"
                for rs in REF_SEEDS[1:]]
    raise ValueError(f"stage must be one of {STAGES}, got {stage!r}")


def stage_dir(root, stage: str, item: str) -> Path:
    return Path(root) / ("sweep" if stage == "selection" else "floor") / item


def clean_file(root, item: str, prompt_seed: int) -> Path:
    """The selecting draw's clean columns sit beside the selection records; the floor stage checks against them."""
    return Path(root) / "sweep" / item / f"clean_s{prompt_seed}.parquet"


def code_rev() -> tuple[str, bool]:
    """(the last commit touching src/lesion/, whether src/lesion/ has uncommitted changes)."""
    rev = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", "src/lesion"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "src/lesion"], text=True).strip())
    return rev, dirty


def check_writable(out_root, allow_dirty: bool) -> str:
    """The code revision to stamp on new cells. Raises ValueError on a dirty
    tree without --allow-dirty, and on --allow-dirty aimed under results/."""
    rev, dirty = code_rev()
    under_results = Path(out_root).resolve().is_relative_to(Path("results").resolve())
    if allow_dirty and under_results:
        raise ValueError("--allow-dirty never writes under results/: use --out-root scratch/E3")
    if dirty and not allow_dirty:
        raise ValueError("src/lesion/ has uncommitted changes: commit them first (--allow-dirty is for smoke runs)")
    return rev


def one_model_revision(records, what: str) -> str:
    """The model revision every input of a derived record was computed at (rule 6). More than one is a hard stop."""
    revs = {r["environment"]["model"]["revision"] for r in records}
    if len(revs) != 1:
        raise ValueError(f"{what}: inputs carry model revisions {sorted(revs)}, expected exactly one")
    return revs.pop()


def item_context(item: str) -> dict:
    """The item's gap and the fraction of the clean ld its scheme removes (D-014 item 2), from the E1b gate."""
    path = ITEM[item].gate_file
    s = json.loads(Path(path).read_text())["statistics"]
    return {"gate_file": path, "gap": s["gap"], "gap_sem": s["gap_sem"], "fraction_removed": s["fraction_removed"]}


# --- files ------------------------------------------------------------------------------------


def _atomic_json(path: Path, record: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(record, indent=2))
    os.replace(tmp, path)


def _atomic_parquet(path: Path, table: pa.Table) -> None:
    tmp = path.with_name(path.name + ".tmp")
    pq.write_table(table, tmp, compression="zstd")
    os.replace(tmp, path)


def load_record(path) -> dict:
    return json.loads(Path(path).read_text())


def write_clean(path: Path, result) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_parquet(path, pa.table({
        "idx": pa.array(range(result.n), pa.int32()), "template": result.templates,
        "ld_clean": pa.array(result.columns["ld_clean"].tolist(), pa.float32()),
        "p_c_clean": pa.array(result.columns["p_c_clean"].tolist(), pa.float32())}))


def load_clean(path) -> dict[str, list]:
    t = pq.read_table(path).to_pydict()
    return {k: t[k] for k in ("template", "ld_clean", "p_c_clean")}


def load_prompts(path) -> dict[str, dict[str, list[float]]]:
    """component label -> {"ld_ablated": [...], "p_c_ablated": [...]}, in prompt order."""
    if not Path(path).exists():
        return {}
    t = pq.read_table(path).to_pydict()
    out: dict[str, dict[str, list[float]]] = {}
    for comp, idx, ld, pc in zip(t["component"], t["idx"], t["ld_ablated"], t["p_c_ablated"]):
        d = out.setdefault(comp, {"ld_ablated": [], "p_c_ablated": []})
        if idx != len(d["ld_ablated"]):
            raise SweepError(f"{path}: prompts of {comp} are not stored in order")
        d["ld_ablated"].append(ld)
        d["p_c_ablated"].append(pc)
    return out


def prompts_table(prompts: dict[str, dict[str, list[float]]]) -> pa.Table:
    comp, idx, ld, pc = [], [], [], []
    for lab in [label(c) for c in COMPONENTS if label(c) in prompts]:
        d = prompts[lab]
        k = len(d["ld_ablated"])
        comp += [lab] * k
        idx += range(k)
        ld += d["ld_ablated"]
        pc += d["p_c_ablated"]
    return pa.table({"component": pa.array(comp, pa.string()).dictionary_encode(), "idx": pa.array(idx, pa.int32()),
                     "ld_ablated": pa.array(ld, pa.float32()), "p_c_ablated": pa.array(pc, pa.float32())})


# --- running ----------------------------------------------------------------------------------


def run_cell_set(model, battery, cs: CellSet, components, out_dir, clean_path, *, n: int, prepend_bos: bool,
                 batch_size: int, keep_prompts: bool, rev: str, command: str, context: dict) -> dict:
    """Run every cell of ``components`` in the cell set ``cs`` that the record
    does not already hold (same spec, same ``rev``), writing after each cell."""
    m = MAP[cs.map_id]
    out_dir, clean_path = Path(out_dir), Path(clean_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, parquet_path = out_dir / f"{cs.stem}.json", out_dir / f"{cs.stem}.parquet"
    config = {"item": cs.item, "scheme": battery.corruption.name, "map": m.id, "kind": m.kind, "value": m.value,
              "frozen": m.frozen, "prompt_seed": cs.prompt_seed, "ref_seed": cs.ref_seed,
              "ref_n": REF_N if m.value == "mean" else None, "n": n, "prepend_bos": prepend_bos,
              "batch_size": batch_size, "keep_prompts": keep_prompts}
    if json_path.exists():
        record = load_record(json_path)
        if record["config"] != config:
            raise SweepError(f"{json_path} was written under a different config; move it away, it is never overwritten")
    else:
        record = {"phase": "E3", "pre_registered": n == N and batch_size == BATCH_SIZE, "config": config,
                  "battery": e1b_gate.battery_record(battery, n, cs.prompt_seed, prepend_bos),
                  "effect_sign": artifact.effect_sign(cell_spec(COMPONENTS[0], m, cs.ref_seed)),
                  "direct_effect_definition": "wang" if m.kind == "direct" else None,
                  "positions": "all", "context": context, "clean_file": str(clean_path),
                  "components": [], "complete": False, "cells": {}}
    prompts = load_prompts(parquet_path) if keep_prompts else {}
    clean = load_clean(clean_path) if clean_path.exists() else None
    t0 = time.time()
    for c in components:
        lab, spec = label(c), cell_spec(c, m, cs.ref_seed)
        old = record["cells"].get(lab)
        if (old is not None and old["spec"] == spec.to_json() and old["code_rev"] == rev
                and (not keep_prompts or lab in prompts)):
            continue
        result = runner.run(model, spec, battery, n, cs.prompt_seed, prepend_bos, batch_size)
        if clean is None:
            write_clean(clean_path, result)
            clean = load_clean(clean_path)
        if (result.columns["ld_clean"].tolist() != clean["ld_clean"]
                or result.columns["p_c_clean"].tolist() != clean["p_c_clean"]):
            raise SweepError(f"{cs.item}/{cs.stem}/{lab}: clean pass differs from {clean_path}")
        if keep_prompts:
            prompts[lab] = {"ld_ablated": result.columns["ld_ablated"].tolist(),
                            "p_c_ablated": result.columns["p_c_ablated"].tolist()}
            _atomic_parquet(parquet_path, prompts_table(prompts))  # prompts first: a cell in the JSON has its prompts
        e = result.aggregates["effect"]
        record["cells"][lab] = {
            "spec": spec.to_json(), "code_rev": rev, "effect_mean": e["ld"]["effect_mean"], "sem": e["ld"]["sem"],
            "clean_mean_ld": result.aggregates["clean"]["mean_ld"],
            "ablated_mean_ld": result.aggregates["ablated"]["mean_ld"], "ratio_of_means": e["ld"]["ratio_of_means"],
            "p_c": e["p_c"], "reference": result.reference_summary, "seconds": result.seconds}
        record["components"] = [label(x) for x in COMPONENTS if label(x) in record["cells"]]
        record["complete"] = len(record["components"]) == len(COMPONENTS)
        record["command"] = command
        record["environment"] = artifact.environment_record(model, batch_size, time.time() - t0)
        _atomic_json(json_path, record)
        print(f"  {cs.item:9} {cs.stem:26} {lab:7} effect {e['ld']['effect_mean']:+.4f} ± {e['ld']['sem']:.4f}"
              f"  [{result.seconds:.1f}s]", flush=True)
    return record


# --- CLI ----------------------------------------------------------------------------------------


def parse_selection(maps: str, components: str) -> tuple[tuple[str, ...] | None, tuple[Component, ...]]:
    chosen_maps = None if maps == "all" else tuple(maps.split(","))
    if chosen_maps is not None:
        unknown = [x for x in chosen_maps if x not in MAP]
        if unknown:
            raise ValueError(f"unknown map(s) {unknown}; maps are {list(MAP)}")
    if components == "all":
        return chosen_maps, COMPONENTS
    comps = tuple(parse_label(x) for x in components.split(","))
    unknown = [label(c) for c in comps if c not in COMPONENTS]
    if unknown:
        raise ValueError(f"unknown component(s) {unknown}")
    return chosen_maps, comps


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e3_sweep", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", required=True, choices=[*ITEM, "all"])
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--maps", default="all", help="comma-separated map ids, or all")
    ap.add_argument("--components", default="all", help="comma-separated labels (L9H6, L0.mlp), or all")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-root", default="results/E3")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="run with uncommitted changes under src/lesion/ (smoke runs; never under results/)")
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = build_parser()
    args = ap.parse_args(argv)
    items = tuple(ITEM) if args.item == "all" else (args.item,)
    try:
        maps, comps = parse_selection(args.maps, args.components)
        if args.n <= 0:
            raise ValueError("--n must be positive")
        rev = check_writable(args.out_root, args.allow_dirty)
        from src.lesion.e1b_noise import require_gate_pass

        for item in items:
            require_gate_pass(Path(ITEM[item].gate_file), ITEM[item].prepend_bos)
    except ValueError as e:
        ap.error(str(e))  # exits 2, before any model loads

    from src.lesion.ablate import make_battery
    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(SEED)
    model = load_model(args.device)
    tok = plain_tokenizer()
    command = "uv run python -m src.lesion.e3_sweep " + " ".join(shlex.quote(a) for a in argv)
    for item in items:
        battery = make_battery(item, tok, None)
        for cs in cell_sets((item,), args.stage, maps):
            run_cell_set(model, battery, cs, comps, stage_dir(args.out_root, args.stage, item),
                         clean_file(args.out_root, item, SEED), n=args.n, prepend_bos=ITEM[item].prepend_bos,
                         batch_size=args.batch_size, keep_prompts=args.stage == "selection", rev=rev,
                         command=command, context=item_context(item))
    return 0


if __name__ == "__main__":
    sys.exit(main())
