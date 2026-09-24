"""E1b gate: per (item, scheme), the clean and the corrupt prompts through the
unmodified model; the pre-registered gate on the default scheme, statistics
for the named extras.

    uv run python -m src.lesion.e1b_gate --item all            # every item, every scheme
    uv run python -m src.lesion.e1b_gate --item ioi --scheme flip

Gate (D-014 item 1; thresholds fixed before any generator ran, never relaxed):
pairwise accuracy mean 1[ld_clean > 0] >= 0.90; gap mean ld_clean - mean
ld_corrupt >= 1.0 logit; factual recall additionally >= 300 admitted
survivors. n = 2,000 for IOI and induction, every admitted survivor for
factual recall; seed 0. A run at any other n or seed records statistics but
no verdict. Also reported, ungated: top-1 rate of c, mean P[c] clean and
corrupt, fraction removed, the per-prompt spread, and per-template
reference counts at the reference n E3 will use, against the floor of 30.

One JSON (+ per-prompt parquet) per (item, scheme) under results/E1b/gate/{item}/."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import torch
from torch import Tensor

from src.lesion.ablate import BATTERIES, make_battery, parse_bool
from src.lesion.battery import TEMPLATE_FLOOR, resolve_scheme
from src.lesion.runner import group_by_length, metrics

ACC_MIN, GAP_MIN, SURVIVORS_MIN = 0.90, 1.0, 300
REF_N, REF_SEED = 2000, 0  # the reference draw E3 uses (O-015 resolution); E1a used 1,000
DEFAULT_N = 2000
ITEMS = ("ioi", "induction", "factual")
THRESHOLDS = {"pairwise_accuracy_min": ACC_MIN, "gap_min": GAP_MIN, "survivors_min": SURVIVORS_MIN,
              "template_floor": TEMPLATE_FLOOR}


@torch.no_grad()
def measure(model, battery, n: int, seed: int, prepend_bos: bool, batch_size: int) -> tuple[dict[str, Tensor], list[str]]:
    """Per prompt: ld and P[c] on the clean and the corrupt prompt (each read
    at its own END), and whether c is the clean top-1 token. The clean pass is
    the call the harness makes (``model(toks)``), so the numbers agree."""
    pairs = battery.pairs(n, seed, prepend_bos)
    cols = {k: torch.empty(n, dtype=torch.float32)
            for k in ("ld_clean", "ld_corrupt", "p_c_clean", "p_c_corrupt", "top1_clean")}
    device = model.cfg.device
    for batch in group_by_length([p.clean_ids for p in pairs], batch_size):
        idx = torch.tensor(batch)
        ans = torch.tensor([pairs[i].answer_id for i in batch], device=device)
        comp = torch.tensor([pairs[i].competitor_id for i in batch], device=device)
        for side, ids_of, labels_of in (("clean", "clean_ids", "positions"), ("corrupt", "corrupt_ids", "corrupt_positions")):
            toks = torch.tensor([getattr(pairs[i], ids_of) for i in batch], device=device)
            end = torch.tensor([getattr(pairs[i], labels_of)["END"] for i in batch], device=device)
            logits = model(toks)
            ld, p_c, _ = metrics(logits, end, ans, comp)
            cols[f"ld_{side}"][idx] = ld
            cols[f"p_c_{side}"][idx] = p_c
            if side == "clean":
                top = logits[torch.arange(len(batch), device=device), end, :].argmax(-1)
                cols["top1_clean"][idx] = (top == ans).float().cpu()
            del logits
    return cols, [p.template for p in pairs]


def statistics(cols: dict[str, Tensor], templates: list[str]) -> dict:
    n = len(templates)
    clean, corrupt = cols["ld_clean"].float(), cols["ld_corrupt"].float()
    diff = clean - corrupt
    mean_clean = clean.mean().item()
    by_template = {}
    for t in sorted(set(templates)):
        m = torch.tensor([x == t for x in templates])
        by_template[t] = {"n": int(m.sum()), "mean_ld_clean": clean[m].mean().item(),
                          "mean_ld_corrupt": corrupt[m].mean().item()}
    side = lambda ld, p: {"mean_ld": ld.mean().item(), "std_ld": ld.std().item(),  # noqa: E731
                          "sem_ld": (ld.std() / n ** 0.5).item(), "mean_p_c": p.float().mean().item()}
    return {
        "n": n,
        "pairwise_accuracy": int((clean > 0).sum()) / n,  # exact ratio: 1800/2000 must read 0.9
        "pairwise_accuracy_corrupt": int((corrupt > 0).sum()) / n,
        "top1_rate": int(cols["top1_clean"].sum()) / n,
        "clean": side(clean, cols["p_c_clean"]),
        "corrupt": side(corrupt, cols["p_c_corrupt"]),
        "gap": diff.mean().item(),
        "gap_sem": (diff.std() / n ** 0.5).item(),
        "fraction_removed": diff.mean().item() / mean_clean if mean_clean != 0 else None,
        "by_template": by_template,
    }


def is_pre_registered(n: int, seed: int, n_admitted: int | None, prepend_bos: bool, default_prepend_bos: bool) -> bool:
    """The gate is defined only at the spec's n and seed -- 2,000 (IOI,
    induction) or every admitted survivor (factual), always at seed 0 -- and
    at the battery's default BOS setting."""
    return seed == 0 and n == (DEFAULT_N if n_admitted is None else n_admitted) and prepend_bos == default_prepend_bos


def verdict(stats: dict | None, survivors: int | None) -> dict:
    def cond(value, threshold):
        return {"value": value, "threshold": threshold, "pass": value is not None and value >= threshold}

    get = (lambda k: None) if stats is None else stats.get
    conds = {"pairwise_accuracy": cond(get("pairwise_accuracy"), ACC_MIN), "gap": cond(get("gap"), GAP_MIN)}
    if survivors is not None:
        conds["survivors"] = cond(survivors, SURVIVORS_MIN)
    return {"conditions": conds, "pass": all(c["pass"] for c in conds.values())}


def reference_floor(battery, ref_n: int, prepend_bos: bool) -> dict:
    counts = dict(sorted(Counter(p.template for p in battery.pairs(ref_n, REF_SEED, prepend_bos)).items()))
    return {"ref_n": ref_n, "ref_seed": REF_SEED, "floor": TEMPLATE_FLOOR, "per_template_counts": counts,
            "min": min(counts.values()), "templates_below_floor": [t for t, k in counts.items() if k < TEMPLATE_FLOOR]}


def battery_record(battery, n: int, seed: int, prepend_bos: bool) -> dict:
    return {"name": battery.name, "n": n, "seed": seed, "prepend_bos": prepend_bos,
            "template_set": battery.template_set, "labels": list(battery.labels), "schemes": list(battery.schemes),
            "corruption": asdict(battery.corruption), "expected_direction": battery.expected_direction}


def write(record: dict, cols: dict[str, Tensor] | None, templates: list[str], out_dir, item: str, scheme: str) -> Path:
    d = Path(out_dir) / item
    d.mkdir(parents=True, exist_ok=True)
    json_path = d / f"{scheme}.json"
    json_path.write_text(json.dumps(record, indent=2))
    if cols is not None:
        table = {"idx": list(range(len(templates))), "template": templates, **{k: v.tolist() for k, v in cols.items()}}
        pq.write_table(pa.table(table), json_path.with_suffix(".parquet"), compression="zstd", compression_level=9)
    return json_path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e1b_gate", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", required=True, choices=[*ITEMS, "all"])
    ap.add_argument("--scheme", default="all", help="a scheme of --item, or 'all' (default)")
    ap.add_argument("--n", type=int, default=None, help="default: 2000; every admitted survivor for factual")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--prepend-bos", default=None, help="true|false (default: the battery's own)")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", default="results/E1b/gate")
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = build_parser()
    args = ap.parse_args(argv)
    items = ITEMS if args.item == "all" else (args.item,)
    try:
        if args.item == "all" and args.scheme != "all":
            raise ValueError("--item all runs every scheme of every item; drop --scheme")
        if args.prepend_bos is not None:
            parse_bool(args.prepend_bos)
        for item in items:
            cls = BATTERIES[item]
            preflight = getattr(cls, "preflight", None)
            if preflight is not None:
                preflight()
            if args.scheme != "all":
                resolve_scheme(cls.schemes, args.scheme)
    except ValueError as e:
        ap.error(str(e))  # exits 2

    from src.lesion import artifact
    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(args.seed)
    model = load_model(args.device)
    tok = plain_tokenizer()
    command = "uv run python -m src.lesion.e1b_gate " + " ".join(shlex.quote(a) for a in argv)
    for item in items:
        cls = BATTERIES[item]
        prepend_bos = cls.default_prepend_bos if args.prepend_bos is None else parse_bool(args.prepend_bos)
        for scheme in (cls.schemes if args.scheme == "all" else (args.scheme,)):
            battery = make_battery(item, tok, scheme)
            n_admitted = getattr(battery, "n_admitted", None)
            n = args.n if args.n is not None else (n_admitted if n_admitted is not None else DEFAULT_N)
            pre_registered = is_pre_registered(n, args.seed, n_admitted, prepend_bos, cls.default_prepend_bos)
            ref_n = REF_N if n_admitted is None else min(REF_N, n_admitted)
            t0 = time.time()
            cols, templates = measure(model, battery, n, args.seed, prepend_bos, args.batch_size) if n > 0 else (None, [])
            stats = statistics(cols, templates) if n > 0 else None
            gated = scheme == cls.schemes[0]
            record = {
                "phase": "E1b", "command": command, "item": item, "scheme": scheme, "gated": gated,
                "pre_registered": pre_registered,
                "thresholds": THRESHOLDS,
                "verdict": verdict(stats, n_admitted) if gated and pre_registered else None,
                "statistics": stats,
                "reference_floor": reference_floor(battery, ref_n, prepend_bos) if ref_n > 0 else None,
                "battery": battery_record(battery, n, args.seed, prepend_bos),
                "environment": artifact.environment_record(model, args.batch_size, time.time() - t0),
            }
            path = write(record, cols, templates, args.out_dir, item, scheme)
            if stats is None:
                line = "no prompts"
            else:
                line = (f"acc {stats['pairwise_accuracy']:.3f}  gap {stats['gap']:+.3f} ± {stats['gap_sem']:.3f}  "
                        f"removed {stats['fraction_removed']:.2f}  top1 {stats['top1_rate']:.3f}")
            if not gated:
                tag = "extra"
            elif not pre_registered:
                tag = "unreg"
            else:
                tag = "PASS" if record["verdict"]["pass"] else "FAIL"
            print(f"{item:9} {scheme:16} {tag:5} n={n:<5} {line}  -> {path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
