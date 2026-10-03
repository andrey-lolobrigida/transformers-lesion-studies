"""E3 validation gates 1-3 (the E3 spec, "Validation gates"). They test the
instrument, not the model; a failure stops the sweep and is debugged as a
harness failure.

    uv run python -m src.lesion.e3_gates --gate all      # or --gate 1 / 2 / 3

1. E1b identity. The 24 E1b noise components (12 MLPs, head 0 of each layer),
   unfrozen node mean at reference seeds 0-4, run through the E3 sweep driver
   on each item, reproduce the per-seed effect_mean and the seed-0 sem of
   results/E1b/noise/{item}/floor.json bitwise. The cells are written where
   the sweep keeps them (sweep/ for seed 0, floor/ for 1-4) and the sweep
   reuses them under resume.
2. E2 identity. E2 I3's single-unit cells (5.5, 6.9, 4.11, 2.2 on induction;
   three values; frozen and unfrozen), through the sweep driver, reproduce the
   per-prompt ld_clean, p_c_clean, ld_ablated and p_c_ablated columns of
   results/E2/I3/ bitwise.
3. Determinism. Each pre-registered determinism cell, run twice in one
   process, gives bitwise identical columns.

Writes results/E3/gates/{e1b_identity,e2_identity,determinism}.json and exits
1 if any gate fails."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq
import torch

from src.lesion import artifact, runner
from src.lesion.e3_prereg import (
    ADV_HEADS, BATCH_SIZE, DETERMINISM_CELLS, GATE1_COMPONENTS, GATE2_DIR, ITEM, ITEMS, MAP, N, REF_SEEDS, SEED,
    VALUES, label, parse_label,
)
from src.lesion.e3_sweep import (
    CellSet, cell_spec, check_writable, clean_file, item_context, load_clean, load_prompts, run_cell_set, stage_dir,
)

GATES = {"1": "e1b_identity", "2": "e2_identity", "3": "determinism"}


@dataclass
class Ctx:
    model: object
    tok: object
    root: Path
    rev: str
    command: str


def compare_floor(floor: dict, recs: dict[int, dict]) -> tuple[int, list[dict]]:
    """Every per-seed effect_mean and the seed-0 sem of an E1b floor record
    against our cell-set records (reference seed -> record), bitwise."""
    compared, mismatches = 0, []
    seeds = sorted(recs)
    for row in floor["rows"]:
        lab = row["component"]
        pairs = [(f"effect_mean@ref{rs}", recs[rs]["cells"][lab]["effect_mean"], row["effect_mean_by_ref_seed"][str(rs)])
                 for rs in seeds]
        pairs.append((f"sem@ref{seeds[0]}", recs[seeds[0]]["cells"][lab]["sem"], row["sem_seed0"]))
        for field, ours, theirs in pairs:
            compared += 1
            if ours != theirs:
                mismatches.append({"component": lab, "field": field, "ours": ours, "theirs": theirs})
    return compared, mismatches


def compare_columns(ours: dict[str, list[float]], theirs: dict[str, list[float]], where: str) -> tuple[int, list[dict]]:
    compared, mismatches = 0, []
    for col, a in ours.items():
        b = theirs[col]
        compared += 1
        if len(a) != len(b):
            mismatches.append({"where": where, "column": col, "first_diff_at": f"length {len(a)} vs {len(b)}"})
        elif a != b:
            k = next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
            mismatches.append({"where": where, "column": col, "first_diff_at": k, "ours": a[k], "theirs": b[k]})
    return compared, mismatches


def _battery(ctx: Ctx, item: str):
    from src.lesion.ablate import make_battery

    return make_battery(item, ctx.tok, None)


def gate1(ctx: Ctx) -> dict:
    m = MAP["total_mean_unfrozen"]
    compared, mismatches, per_item = 0, [], {}
    for item in ITEMS:
        floor = json.loads(Path(item.floor_file).read_text())
        if (floor["n"], floor["seed"], floor["ref_n"], floor["battery"]["prepend_bos"]) != (N, SEED, 2000, item.prepend_bos):
            mismatches.append({"item": item.name, "field": "config", "theirs": [floor["n"], floor["seed"], floor["ref_n"]]})
            continue
        battery = _battery(ctx, item.name)
        recs = {}
        for rs in REF_SEEDS:
            stage = "selection" if rs == REF_SEEDS[0] else "floor"
            recs[rs] = run_cell_set(ctx.model, battery, CellSet(item.name, m.id, SEED, rs), GATE1_COMPONENTS,
                                    stage_dir(ctx.root, stage, item.name), clean_file(ctx.root, item.name, SEED),
                                    n=N, prepend_bos=item.prepend_bos, batch_size=BATCH_SIZE,
                                    keep_prompts=stage == "selection", rev=ctx.rev, command=ctx.command,
                                    context=item_context(item.name))
        c, mm = compare_floor(floor, recs)
        compared += c
        mismatches += [{"item": item.name, **x} for x in mm]
        per_item[item.name] = {"floor_file": item.floor_file, "compared": c, "mismatches": len(mm)}
    return {"gate": GATES["1"], "pass": not mismatches and compared == 3 * 24 * 6, "compared": compared,
            "per_item": per_item, "mismatches": mismatches}


def gate2(ctx: Ctx) -> dict:
    item = ITEM["induction"]
    battery = _battery(ctx, "induction")
    compared, mismatches = 0, []
    for frozen in (False, True):
        for v in VALUES:
            m = MAP[f"total_{v}_{'frozen' if frozen else 'unfrozen'}"]
            rs = REF_SEEDS[0] if v == "mean" else None
            cs = CellSet("induction", m.id, SEED, rs)
            out = stage_dir(ctx.root, "selection", "induction")
            run_cell_set(ctx.model, battery, cs, ADV_HEADS, out, clean_file(ctx.root, "induction", SEED), n=N,
                         prepend_bos=item.prepend_bos, batch_size=BATCH_SIZE, keep_prompts=True, rev=ctx.rev,
                         command=ctx.command, context=item_context("induction"))
            prompts = load_prompts(out / f"{cs.stem}.parquet")
            clean = load_clean(clean_file(ctx.root, "induction", SEED))
            for h in ADV_HEADS:
                lab = label(h)
                e2_path = Path(GATE2_DIR) / (artifact.stem(cell_spec(h, m, rs), "induction", N, SEED, True) + ".parquet")
                theirs = pq.read_table(e2_path).to_pydict()
                ours = {"ld_clean": clean["ld_clean"], "p_c_clean": clean["p_c_clean"],
                        "ld_ablated": prompts[lab]["ld_ablated"], "p_c_ablated": prompts[lab]["p_c_ablated"]}
                c, mm = compare_columns(ours, theirs, f"{m.id}/{lab} vs {e2_path}")
                compared += c
                mismatches += mm
    return {"gate": GATES["2"], "pass": not mismatches and compared == 4 * 6 * 4, "compared": compared,
            "mismatches": mismatches}


def gate3(ctx: Ctx) -> dict:
    rows = []
    for item, map_id, lab in DETERMINISM_CELLS:
        m = MAP[map_id]
        spec = cell_spec(parse_label(lab), m, REF_SEEDS[0] if m.value == "mean" else None)
        battery = _battery(ctx, item)
        a = runner.run(ctx.model, spec, battery, N, SEED, ITEM[item].prepend_bos, BATCH_SIZE)
        b = runner.run(ctx.model, spec, battery, N, SEED, ITEM[item].prepend_bos, BATCH_SIZE)
        same = {k: torch.equal(a.columns[k], b.columns[k]) for k in runner.COLUMNS}
        rows.append({"item": item, "map": map_id, "component": lab, "columns_identical": same,
                     "effect_mean": a.aggregates["effect"]["ld"]["effect_mean"]})
    return {"gate": GATES["3"], "pass": all(all(r["columns_identical"].values()) for r in rows),
            "compared": len(rows), "rows": rows}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e3_gates", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", required=True, choices=[*GATES, "all"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-root", default="results/E3")
    args = ap.parse_args(argv)
    try:
        rev = check_writable(args.out_root, allow_dirty=False)
    except ValueError as e:
        ap.error(str(e))

    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(SEED)
    ctx = Ctx(model=load_model(args.device), tok=plain_tokenizer(), root=Path(args.out_root), rev=rev,
              command="uv run python -m src.lesion.e3_gates " + " ".join(shlex.quote(a) for a in argv))
    funcs = {"1": gate1, "2": gate2, "3": gate3}
    out = Path(args.out_root) / "gates"
    out.mkdir(parents=True, exist_ok=True)
    ok = True
    for g in (GATES if args.gate == "all" else (args.gate,)):
        t0 = time.time()
        res = funcs[g](ctx)
        res.update(phase="E3", command=ctx.command, code_rev=rev,
                   environment=artifact.environment_record(ctx.model, BATCH_SIZE, time.time() - t0))
        (out / f"{GATES[g]}.json").write_text(json.dumps(res, indent=2))
        ok = ok and res["pass"]
        print(f"gate {g} {GATES[g]:13} {'PASS' if res['pass'] else 'FAIL'}  compared {res['compared']}"
              f"  -> {out / (GATES[g] + '.json')}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
