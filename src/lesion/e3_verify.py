"""E3 verification (D-016 items 5-6): the shuffle_prefix gate, held-out
replication, restore-clean patching, the induction adversarial checks, and the
exit tables.

    uv run python -m src.lesion.e3_verify --stage gate-shuffle
    uv run python -m src.lesion.e3_verify --stage replicate   --list confirmatory   # or exploratory
    uv run python -m src.lesion.e3_verify --stage restore     --list confirmatory
    uv run python -m src.lesion.e3_verify --stage adversarial
    uv run python -m src.lesion.e3_verify --stage table

Replication gates naming: each selection re-run under its selecting cell
set's settings on prompt seed 1 (mean: reference seed 5 for the effect, 5-9
for s); replicated iff same sign and clears Holm over the list's verification
family. Restore-clean never gates: resample from the clean prompt onto the
corrupt one, node, all positions, unfrozen, prompt seed 1, per selected
component and per item for the set of replicated heads; reported as the
fraction of the gap restored, with its own Holm test (sufficiency family).
Adversarial (induction, measured, never gating): shuffle_prefix and END-only
arms against the fresh_prefix all-position baseline, on the selecting draw,
for E2 I3's units and every induction selection.

The exit tables are built from the replication, restore and adversarial
records, without the model. Each carries the command, the code revision that
wrote it (src/lesion/ must be committed), both seeds, the model revision of
its inputs, and each input's code revision (rule 6)."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from src.lesion import artifact, e1b_gate, runner
from src.lesion.e3_prereg import (
    ADV_ARMS, ADV_HEADS, ADV_SET, ALPHA, BATCH_SIZE, COMPONENTS, HELD_OUT_REF_SEEDS, HELD_OUT_SEED, ITEM, MAP, N,
    REF_N, REF_SEEDS, SEED, SHUFFLE_SCHEME, TOTAL_MAPS, label, parse_label,
)
from src.lesion.e3_select import LISTS, SelectionError, load_list
from src.lesion.e3_stats import cell_s, fraction_restored, holm, z_test
from src.lesion.e3_sweep import (
    CellSet, cell_spec, check_writable, item_context, load_record, one_model_revision, run_cell_set, stage_dir,
)
from src.lesion.knockout import KnockoutSetSpec, Member, run_set
from src.lesion.spec import AblationSpec, All, Head, Labels, MeanReference

STAGES = ("gate-shuffle", "replicate", "restore", "adversarial", "table")
ARM_SETTINGS = {"baseline": ("fresh_prefix", All()), "shuffle_prefix": (SHUFFLE_SCHEME, All()),
                "end_only": ("fresh_prefix", Labels(("END",)))}


class VerifyError(RuntimeError):
    """An instrument check inside verification failed. A hard stop."""


@dataclass
class Ctx:
    model: object
    tok: object
    n: int
    batch_size: int
    root: Path | None
    rev: str
    command: str
    pre_registered: bool


def _battery(ctx: Ctx, item: str, scheme: str | None = None):
    from src.lesion.ablate import make_battery

    return make_battery(item, ctx.tok, scheme)


def _holm_into(rows: list[dict], key, get_p, put) -> None:
    h = holm({key(r): get_p(r) for r in rows}, ALPHA)
    for r in rows:
        put(r, h[key(r)])


def _order(lab: str) -> int:
    return COMPONENTS.index(parse_label(lab))


# --- pure row builders ------------------------------------------------------------------------


def replication_rows(selections: list[dict], held: dict[str, dict], family: str) -> list[dict]:
    """``held``: selection id -> {"effect", "sem", "ref_effects"} on the held-out draw."""
    rows = []
    for s in selections:
        h = held[s["id"]]
        st = cell_s(h["sem"], h["ref_effects"])
        rows.append({"id": s["id"], "item": s["item"], "map": s["map"], "component": s["component"],
                     "effect": s["effect"], "s": s["s"], "selection_rank": s.get("rank"),
                     "held_out": {"effect": h["effect"], **st, **z_test(h["effect"], st["s"])}, "family": family})

    def put(r, h):
        r["held_out"].update(reject=h["reject"], holm_step=h["step"], holm_threshold=h["threshold"])
        same_sign = r["held_out"]["effect"] != 0 and (r["held_out"]["effect"] > 0) == (r["effect"] > 0)
        r["verdict"] = "replicated" if same_sign and h["reject"] else "not replicated"

    _holm_into(rows, lambda r: r["id"], lambda r: r["held_out"]["p"], put)
    return rows


def sufficiency_rows(runs: list[dict], family: str) -> list[dict]:
    rows = [{**r, **z_test(r["effect"], r["sem"]), **fraction_restored(r["effect"], r["sem"], r["gap"]),
             "family": family} for r in runs]
    _holm_into(rows, lambda r: r["id"], lambda r: r["p"],
               lambda r, h: r.update(reject=h["reject"], holm_step=h["step"], holm_threshold=h["threshold"]))
    return rows


def adversarial_units(confirmatory: list[dict], exploratory: list[dict]) -> list[dict]:
    """E2 I3's units under all six total-effect maps, then every induction
    selection under its own map; deduplicated by (unit, map), sources merged."""
    units: dict[tuple[str, str], dict] = {}

    def add(unit: str, members: list[str], map_id: str, source: str) -> None:
        u = units.setdefault((unit, map_id), {"unit": unit, "members": members, "map": map_id, "sources": []})
        if source not in u["sources"]:
            u["sources"].append(source)

    for h in ADV_HEADS:
        for m in TOTAL_MAPS:
            add(label(h), [label(h)], m.id, "E2 I3")
    set_name = "set:" + "+".join(label(h) for h in ADV_SET)
    for m in TOTAL_MAPS:
        add(set_name, [label(h) for h in ADV_SET], m.id, "E2 I3")
    for source, sels in (("confirmatory", confirmatory), ("exploratory", exploratory)):
        for s in sels:
            if s["item"] == "induction":
                add(s["component"], [s["component"]], s["map"], source)
    return list(units.values())


def adversarial_rows(arms: list[dict]) -> list[dict]:
    """The shuffle_prefix and END-only arms are tested (one family); the
    baseline arm is not (its cell is in the main family)."""
    base = {(a["unit"], a["map"]): a for a in arms if a["arm"] == "baseline"}
    rows = []
    for a in arms:
        row = {**a, **cell_s(a["sem"], a["ref_effects"])}
        if a["arm"] != "baseline":
            b = base[(a["unit"], a["map"])]
            row.update(z_test(a["effect"], row["s"]))
            row["baseline_effect"] = b["effect"]
            row["sign_vs_baseline"] = ("zero" if a["effect"] == 0 or b["effect"] == 0 else
                                       "same" if (a["effect"] > 0) == (b["effect"] > 0) else "flipped")
        rows.append(row)
    tested = [r for r in rows if r["arm"] != "baseline"]
    _holm_into(tested, lambda r: f"{r['unit']}|{r['map']}|{r['arm']}", lambda r: r["p"],
               lambda r, h: r.update(reject=h["reject"], holm_step=h["step"], holm_threshold=h["threshold"],
                                     family="adversarial"))
    return rows


def exit_rows(replication: list[dict], restore: list[dict], adversarial: list[dict]) -> list[dict]:
    singles = {r["id"]: r for r in restore if r["kind"] == "single"}
    arms: dict[tuple[str, str], dict] = {}
    for a in adversarial:
        arms.setdefault((a["unit"], a["map"]), {})[a["arm"]] = a
    rows = []
    for r in replication:
        rr = singles.get(f"{r['item']}/{r['component']}")
        row = {"id": r["id"], "item": r["item"], "map": r["map"], "component": r["component"],
               "selection": {"effect": r["effect"], "s": r["s"], "rank": r["selection_rank"]},
               "held_out": {k: r["held_out"][k] for k in ("effect", "s", "z", "reject")}, "verdict": r["verdict"],
               "restore": None if rr is None else {k: rr[k] for k in ("fraction_restored", "fraction_sem", "z",
                                                                        "reject")}}
        if r["item"] == "induction":
            got = arms.get((r["component"], r["map"]), {})
            row["adversarial"] = {arm: None if arm not in got else
                                  {k: got[arm][k] for k in ("effect", "s", "reject", "sign_vs_baseline")}
                                  for arm in ADV_ARMS}
        rows.append(row)
    return rows


# --- runs ---------------------------------------------------------------------------------------


def restore_spec(component) -> AblationSpec:
    return AblationSpec(component=component, value="resample", reference=None, component_type="node", receiver=None,
                        mlp_convention=None, positions=All(), direction="restore-clean", freeze_patterns=False)


def run_arm(ctx: Ctx, unit: dict, arm: str, batteries: dict) -> dict:
    """One adversarial arm of one unit on the selecting draw (BOS, induction).
    Mean maps run at reference seeds 0-4: the effect at 0, the spread over all five."""
    scheme, positions = ARM_SETTINGS[arm]
    battery, m = batteries[scheme], MAP[unit["map"]]
    effects, sem0, reference = [], None, None
    for rs in (REF_SEEDS if m.value == "mean" else (None,)):
        if len(unit["members"]) == 1:
            spec = cell_spec(parse_label(unit["members"][0]), m, rs, positions=positions)
            res = runner.run(ctx.model, spec, battery, ctx.n, SEED, True, ctx.batch_size)
        else:
            ref = MeanReference("corrupt", REF_N, rs, "template") if m.value == "mean" else None
            spec = KnockoutSetSpec(members=tuple(Member(parse_label(x), positions) for x in unit["members"]),
                                   complement=False, value=m.value, reference=ref, direction="ablate-clean",
                                   freeze_patterns=m.frozen, granularity="heads")
            res = run_set(ctx.model, spec, battery, ctx.n, SEED, True, ctx.batch_size)
        e = res.aggregates["effect"]["ld"]
        effects.append(e["effect_mean"])
        if sem0 is None:
            sem0, reference = e["sem"], res.reference_summary
        print(f"  {unit['unit']:14} {unit['map']:24} {arm:15} ref {rs}: effect {e['effect_mean']:+.4f} ± {e['sem']:.4f}",
              flush=True)
    return {"unit": unit["unit"], "members": unit["members"], "map": unit["map"], "arm": arm, "scheme": scheme,
            "positions": "all" if isinstance(positions, All) else "END", "effect": effects[0], "sem": sem0,
            "ref_effects": effects if m.value == "mean" else None, "reference": reference,
            "sources": unit["sources"]}


def check_baseline(root, row: dict) -> None:
    """A single component's baseline arm must reproduce its seed-0 sweep cell bitwise."""
    if len(row["members"]) != 1:
        return
    m = MAP[row["map"]]
    cs = CellSet("induction", m.id, SEED, REF_SEEDS[0] if m.value == "mean" else None)
    cell = load_record(stage_dir(root, "selection", "induction") / f"{cs.stem}.json")["cells"][row["members"][0]]
    if cell["effect_mean"] != row["effect"]:
        raise VerifyError(f"baseline {row['unit']} under {row['map']} does not reproduce the sweep cell: "
                          f"{row['effect']!r} vs {cell['effect_mean']!r}")


def run_gate_shuffle(ctx: Ctx) -> dict:
    """D-014's gate on shuffle_prefix, thresholds unchanged, at n = 2,000, seed 0, BOS."""
    battery = _battery(ctx, "induction", SHUFFLE_SCHEME)
    t0 = time.time()
    cols, templates = e1b_gate.measure(ctx.model, battery, ctx.n, SEED, True, ctx.batch_size)
    stats = e1b_gate.statistics(cols, templates)
    record = {"phase": "E3", "command": ctx.command, "item": "induction", "scheme": SHUFFLE_SCHEME, "gated": True,
              "pre_registered": ctx.pre_registered, "thresholds": e1b_gate.THRESHOLDS,
              "verdict": e1b_gate.verdict(stats, None) if ctx.pre_registered else None, "statistics": stats,
              "prediction": "corrupt mean ld near 0 by symmetry (both c and s stay in context)",
              "reference_floor": e1b_gate.reference_floor(battery, REF_N, True),
              "battery": e1b_gate.battery_record(battery, ctx.n, SEED, True),
              "environment": artifact.environment_record(ctx.model, ctx.batch_size, time.time() - t0)}
    path = e1b_gate.write(record, cols, templates, ctx.root / "gates", "induction", SHUFFLE_SCHEME)
    v = record["verdict"]
    print(f"shuffle_prefix gate: {'unregistered' if v is None else 'PASS' if v['pass'] else 'FAIL'}  "
          f"acc {stats['pairwise_accuracy']:.3f}  gap {stats['gap']:+.3f} ± {stats['gap_sem']:.3f}  "
          f"corrupt ld {stats['corrupt']['mean_ld']:+.3f}  -> {path}", flush=True)
    return record


def prompt_overlap(ctx: Ctx, items) -> dict:
    """Held-out clean prompts that also occur in the selecting draw (IOI's prompt space is finite)."""
    out = {}
    for item in items:
        b, bos = _battery(ctx, item), ITEM[item].prepend_bos
        seen = {p.clean_ids for p in b.pairs(ctx.n, SEED, bos)}
        out[item] = {"n": ctx.n, "held_out_prompts_also_in_selecting_draw":
                     sum(p.clean_ids in seen for p in b.pairs(ctx.n, HELD_OUT_SEED, bos))}
    return out


def run_replicate(ctx: Ctx, name: str) -> dict:
    t0 = time.time()
    sels = load_list(ctx.root, name)
    groups: dict[tuple[str, str], list] = {}
    for s in sels:
        groups.setdefault((s["item"], s["map"]), []).append(parse_label(s["component"]))
    held = {}
    for (item, map_id), comps in groups.items():
        m, battery = MAP[map_id], _battery(ctx, item)
        out = ctx.root / "verify" / name / "heldout" / item
        seeds = HELD_OUT_REF_SEEDS if m.value == "mean" else (None,)
        recs = {rs: run_cell_set(ctx.model, battery, CellSet(item, map_id, HELD_OUT_SEED, rs), comps, out,
                                 out / f"clean_s{HELD_OUT_SEED}.parquet", n=ctx.n, prepend_bos=ITEM[item].prepend_bos,
                                 batch_size=ctx.batch_size, keep_prompts=rs in (None, HELD_OUT_REF_SEEDS[0]),
                                 rev=ctx.rev, command=ctx.command, context=item_context(item)) for rs in seeds}
        for c in comps:
            first = recs[seeds[0]]["cells"][label(c)]
            held[f"{item}/{map_id}/{label(c)}"] = {
                "effect": first["effect_mean"], "sem": first["sem"],
                "ref_effects": [recs[rs]["cells"][label(c)]["effect_mean"] for rs in seeds] if m.value == "mean" else None}
    rows = replication_rows(sels, held, f"verify_{name}")
    record = {"phase": "E3", "command": ctx.command, "pre_registered": ctx.pre_registered, "list": name,
              "code_rev": ctx.rev, "family": f"verify_{name}", "alpha": ALPHA, "prompt_seed": HELD_OUT_SEED,
              "ref_seeds": list(HELD_OUT_REF_SEEDS), "overlap": prompt_overlap(ctx, sorted({s["item"] for s in sels})),
              "n_replicated": sum(r["verdict"] == "replicated" for r in rows),
              "environment": artifact.environment_record(ctx.model, ctx.batch_size, time.time() - t0), "rows": rows}
    path = ctx.root / "verify" / name / "replication.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2))
    print(f"{name}: {record['n_replicated']}/{len(rows)} replicated -> {path}", flush=True)
    return record


def _write_run(ctx: Ctx, result, spec, battery, out: Path, base: str | None = None) -> None:
    env = artifact.environment_record(ctx.model, ctx.batch_size, result.seconds)
    rec = artifact.build_record(result, spec, battery, ctx.command, env, {"stage": "restore"}, phase="E3")
    rec["pre_registered"] = ctx.pre_registered
    artifact.write(rec, result, out, base=base)


def run_restore(ctx: Ctx, name: str) -> dict:
    t0 = time.time()
    sels = load_list(ctx.root, name)
    repl = json.loads((ctx.root / "verify" / name / "replication.json").read_text())["rows"]
    out = ctx.root / "verify" / name / "restore"
    items = sorted({s["item"] for s in sels}, key=lambda i: list(ITEM).index(i))
    batteries = {i: _battery(ctx, i) for i in items}
    gaps = {}
    for item in items:
        cols, templates = e1b_gate.measure(ctx.model, batteries[item], ctx.n, HELD_OUT_SEED, ITEM[item].prepend_bos,
                                           ctx.batch_size)
        st = e1b_gate.statistics(cols, templates)
        gaps[item] = {"gap": st["gap"], "gap_sem": st["gap_sem"], "fraction_removed": st["fraction_removed"],
                      "mean_ld_clean": st["clean"]["mean_ld"], "mean_ld_corrupt": st["corrupt"]["mean_ld"]}
    runs = []
    for item, lab in sorted({(s["item"], s["component"]) for s in sels}, key=lambda x: (items.index(x[0]), _order(x[1]))):
        spec = restore_spec(parse_label(lab))
        result = runner.run(ctx.model, spec, batteries[item], ctx.n, HELD_OUT_SEED, ITEM[item].prepend_bos,
                            ctx.batch_size)
        _write_run(ctx, result, spec, batteries[item], out)
        e = result.aggregates["effect"]["ld"]
        runs.append({"id": f"{item}/{lab}", "kind": "single", "item": item, "components": [lab],
                     "effect": e["effect_mean"], "sem": e["sem"], "gap": gaps[item]["gap"],
                     "restored_mean_ld": result.aggregates["ablated"]["mean_ld"],
                     "corrupt_mean_ld": result.aggregates["clean"]["mean_ld"]})
        print(f"  restore {item:9} {lab:7} effect {e['effect_mean']:+.4f} ± {e['sem']:.4f}", flush=True)
    for item in items:
        replicated = sorted({r["component"] for r in repl if r["item"] == item and r["verdict"] == "replicated"},
                            key=_order)
        heads = [x for x in replicated if isinstance(parse_label(x), Head)]
        left_out = [x for x in replicated if x not in heads]
        if not heads:
            continue
        spec = KnockoutSetSpec(members=tuple(Member(parse_label(x), All()) for x in heads), complement=False,
                               value="resample", reference=None, direction="restore-clean", freeze_patterns=False,
                               granularity="heads")
        result = run_set(ctx.model, spec, batteries[item], ctx.n, HELD_OUT_SEED, ITEM[item].prepend_bos,
                         ctx.batch_size)
        _write_run(ctx, result, spec, batteries[item], out,
                   base=artifact.set_stem(spec, item, f"replicated-{name}", ctx.n, HELD_OUT_SEED,
                                          ITEM[item].prepend_bos))
        e = result.aggregates["effect"]["ld"]
        runs.append({"id": f"{item}/set", "kind": "set", "item": item, "components": heads,
                     "mlps_left_out": left_out, "effect": e["effect_mean"], "sem": e["sem"], "gap": gaps[item]["gap"],
                     "restored_mean_ld": result.aggregates["ablated"]["mean_ld"],
                     "corrupt_mean_ld": result.aggregates["clean"]["mean_ld"]})
    rows = sufficiency_rows(runs, f"sufficiency_{name}")
    record = {"phase": "E3", "command": ctx.command, "pre_registered": ctx.pre_registered, "list": name,
              "code_rev": ctx.rev, "family": f"sufficiency_{name}", "alpha": ALPHA, "prompt_seed": HELD_OUT_SEED,
              "definition": "restore-clean: resample from the clean prompt onto the corrupt prompt, node, all "
                            "positions, unfrozen; fraction restored = -effect / gap, gap measured on the same draw",
              "environment": artifact.environment_record(ctx.model, ctx.batch_size, time.time() - t0),
              "gaps": gaps, "rows": rows}
    path = ctx.root / "verify" / name / "restore.json"
    path.write_text(json.dumps(record, indent=2))
    print(f"{name}: {len(rows)} restore rows -> {path}", flush=True)
    return record


def load_persisted_arms(path: Path, rev: str) -> dict[tuple, dict]:
    """Arms already finished under this code revision, keyed (unit, map, arm); stale-revision lines are ignored."""
    out: dict[tuple, dict] = {}
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("code_rev") == rev:
                    out[(r["unit"], r["map"], r["arm"])] = {k: v for k, v in r.items() if k != "code_rev"}
    return out


def run_adversarial(ctx: Ctx) -> dict:
    t0 = time.time()
    gate = json.loads((ctx.root / "gates" / "induction" / f"{SHUFFLE_SCHEME}.json").read_text())
    shuffle_ok = gate["verdict"] is not None and gate["verdict"]["pass"]
    conf = load_list(ctx.root, "confirmatory")
    expl = load_list(ctx.root, "exploratory") if (ctx.root / "selection" / "exploratory.json").exists() else []
    units = adversarial_units(conf, expl)
    batteries = {"fresh_prefix": _battery(ctx, "induction")}
    arms = ["baseline", "end_only"]
    if shuffle_ok:
        batteries[SHUFFLE_SCHEME] = _battery(ctx, "induction", SHUFFLE_SCHEME)
        arms.insert(1, SHUFFLE_SCHEME)
    arms_path = ctx.root / "adversarial" / "arms.jsonl"
    arms_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_persisted_arms(arms_path, ctx.rev)
    runs = []
    for u in units:
        for arm in arms:
            r = done.get((u["unit"], u["map"], arm))
            if r is None:
                r = run_arm(ctx, u, arm, batteries)
                with arms_path.open("a") as f:
                    f.write(json.dumps({**r, "code_rev": ctx.rev}) + "\n")
            else:
                print(f"  reused {u['unit']:14} {u['map']:24} {arm}", flush=True)
            if arm == "baseline":
                check_baseline(ctx.root, r)
            runs.append(r)
    record = {"phase": "E3", "command": ctx.command, "pre_registered": ctx.pre_registered, "family": "adversarial",
              "code_rev": ctx.rev, "alpha": ALPHA, "prompt_seed": SEED,
              "environment": artifact.environment_record(ctx.model, ctx.batch_size, time.time() - t0),
              "shuffle_gate": {"pass": shuffle_ok,
                               "note": None if shuffle_ok else "shuffle_prefix failed its gate or has no verdict; "
                                                               "its arm was not run (logged as a null)"},
              "units": units, "rows": adversarial_rows(runs)}
    path = ctx.root / "adversarial" / "adversarial.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2))
    print(f"adversarial: {len(units)} units x {len(arms)} arms -> {path}", flush=True)
    return record


def write_tables(root, command: str, rev: str) -> list[Path]:
    root = Path(root)
    adv_path = root / "adversarial" / "adversarial.json"
    adv_rec = json.loads(adv_path.read_text()) if adv_path.exists() else None
    adv = adv_rec["rows"] if adv_rec else []
    written = []
    for name in LISTS:
        rp, sp = root / "verify" / name / "replication.json", root / "verify" / name / "restore.json"
        if not rp.exists():
            continue
        inputs = {p: json.loads(p.read_text()) for p in (rp, sp) if p.exists()}
        if adv_rec:
            inputs[adv_path] = adv_rec
        restore = inputs[sp]["rows"] if sp in inputs else []
        sets = [r for r in restore if r["kind"] == "set"]
        rows = exit_rows(inputs[rp]["rows"], restore, adv)
        path = root / f"exit_{name}.json"
        record = {"phase": "E3", "command": command, "code_rev": rev, "prompt_seed": SEED,
                  "held_out_seed": HELD_OUT_SEED, "model_revision": one_model_revision(inputs.values(), path.name),
                  "inputs": {p.relative_to(root).as_posix(): {"code_rev": r["code_rev"]} for p, r in inputs.items()},
                  "list": name, "rows": rows, "set_restores": sets}
        path.write_text(json.dumps(record, indent=2))
        written.append(path)
        print(f"{name}: {len(rows)} rows -> {path}")
    return written


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e3_verify", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--list", choices=LISTS, default="confirmatory")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-root", default="results/E3")
    args = ap.parse_args(argv)
    root = Path(args.out_root)
    command = "uv run python -m src.lesion.e3_verify " + " ".join(shlex.quote(a) for a in argv)
    try:
        if args.n <= 0:
            raise ValueError("--n must be positive")
        rev = check_writable(root, allow_dirty=False)
        if args.stage == "table":
            write_tables(root, command, rev)
            return 0
        if args.stage in ("replicate", "restore"):
            load_list(root, args.list)
        if args.stage == "restore" and not (root / "verify" / args.list / "replication.json").exists():
            raise ValueError(f"run --stage replicate --list {args.list} first")
        if args.stage == "adversarial":
            if not (root / "gates" / "induction" / f"{SHUFFLE_SCHEME}.json").exists():
                raise ValueError("run --stage gate-shuffle first")
            load_list(root, "confirmatory")
            if (root / "selection" / "exploratory.json").exists():
                load_list(root, "exploratory")
    except (ValueError, SelectionError) as e:
        ap.error(str(e))  # exits 2, before any model loads

    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(SEED)
    ctx = Ctx(model=load_model(args.device), tok=plain_tokenizer(), n=args.n, batch_size=args.batch_size, root=root,
              rev=rev, command=command,
              pre_registered=args.n == N and args.batch_size == BATCH_SIZE)
    if args.stage == "gate-shuffle":
        run_gate_shuffle(ctx)
    elif args.stage == "replicate":
        run_replicate(ctx, args.list)
    elif args.stage == "restore":
        run_restore(ctx, args.list)
    else:
        run_adversarial(ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
