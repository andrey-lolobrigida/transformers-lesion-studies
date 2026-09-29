"""E2 targets (I1-I4, P1-P4). Each ``target_*`` runs its measurements, writes
its artifacts under ``{out_dir}/{target}/`` (every one with a top-level
``pre_registered``), and returns its verdict entries; ``e2_reproduce.main``
writes ``verdict.json``. Constants and rules: ``e2_reproduce.py``."""

from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import torch

from src.lesion import artifact, e1b_gate
from src.lesion.battery import TEMPLATE_FLOOR
from src.lesion.e2_reproduce import (
    ALL_HEADS, CLASS, CLASSES, CORNERS, I1_BOS, I1_DEFINITIONS, I1_HALF_LEN, I1_N_SEQ, I1_ROWS, I1_SPREAD_SEEDS,
    I2_BASELINE_DRAWS, I2_BASELINE_SEED, I2_RECEIVERS, I2_ROUTES, I2_SENDERS, I3_HEADS, I3_SET, I4_MEMBERS,
    INDUCTION_BOS, IOI_BOS, MATCHED, MEASURED, NOT_MATCHED, P1_FUZZY, P1_ROWS, P1_SIGN, P1_SWEEPS, P2_PUBLISHED,
    P3_CONTRAST, P3_PUBLISHED, P3_PUBLISHED_ABS_GAP, REF_N, REF_SEED, VALUES, check_direct_path, entry, floor_for,
    identity_verdict, label, magnitude_verdict, ranks, sign_verdict,
)
from src.lesion.evaluators import (
    attention_scores, composition_scores, copy_scores, random_baseline, repeated_random_tokens,
)
from src.lesion.induction import InductionBattery
from src.lesion.ioi import IOIBattery
from src.lesion.knockout import KnockoutSetSpec, Member, run_set
from src.lesion.runner import run
from src.lesion.spec import AblationSpec, All, Head, Labels, Logits, MeanReference

I1_BATCH = 20  # 201-token sequences


@dataclass
class Ctx:
    model: object
    tok: object
    n: int
    seed: int
    batch_size: int
    out_dir: Path
    command: str
    cli: dict
    pre_registered: bool
    resume: bool = False


# --- specs ------------------------------------------------------------------------------


def mean_ref(ref_n: int = REF_N) -> MeanReference:
    return MeanReference("corrupt", ref_n, REF_SEED, "template")


def ref_for(value: str, ref_n: int = REF_N) -> MeanReference | None:
    return mean_ref(ref_n) if value == "mean" else None


def node_spec(h: Head, value: str, positions, direction: str = "ablate-clean", freeze: bool = False,
              ref_n: int = REF_N) -> AblationSpec:
    return AblationSpec(component=h, value=value, reference=ref_for(value, ref_n), component_type="node",
                        receiver=None, mlp_convention=None, positions=positions, direction=direction,
                        freeze_patterns=freeze)


def edge_spec(h: Head, value: str, sender_position: str, receiver, ref_n: int = REF_N) -> AblationSpec:
    """Wang's path patching: edge, MLPs recompute, the sender at the receiver's position."""
    check_direct_path(sender_position, receiver)
    return AblationSpec(component=h, value=value, reference=ref_for(value, ref_n), component_type="edge",
                        receiver=receiver, mlp_convention="wang", positions=Labels((sender_position,)),
                        direction="ablate-clean", freeze_patterns=False)


def set_spec(members, value: str, direction: str = "ablate-clean", freeze: bool = False, complement: bool = False,
             ref_n: int = REF_N) -> KnockoutSetSpec:
    return KnockoutSetSpec(members=tuple(members), complement=complement, value=value, reference=ref_for(value, ref_n),
                           direction=direction, freeze_patterns=freeze, granularity="heads")


def ioi(ctx: Ctx, templates_per_order: int = 15) -> IOIBattery:
    return IOIBattery(ctx.tok, "p_ABC", templates_per_order=templates_per_order)


def induction(ctx: Ctx) -> InductionBattery:
    return InductionBattery(ctx.tok)


# --- runs and records ----------------------------------------------------------------------


def _finish(ctx: Ctx, result, spec, battery) -> dict:
    env = artifact.environment_record(ctx.model, ctx.batch_size, result.seconds)
    record = artifact.build_record(result, spec, battery, ctx.command, env, ctx.cli, phase="E2")
    record["pre_registered"] = ctx.pre_registered
    return record


def _log(path: Path, record: dict) -> None:
    e = record["results"]["effect"]["ld"]
    print(f"  effect {e['effect_mean']:+.4f} ± {e['sem']:.4f}  -> {path}", flush=True)


def run_single(ctx: Ctx, spec: AblationSpec, battery, prepend_bos: bool, out_dir: Path) -> dict:
    result = run(ctx.model, spec, battery, ctx.n, ctx.seed, prepend_bos, ctx.batch_size)
    record = _finish(ctx, result, spec, battery)
    json_path, _ = artifact.write(record, result, out_dir)
    _log(json_path, record)
    return record


def run_set_named(ctx: Ctx, spec: KnockoutSetSpec, battery, prepend_bos: bool, out_dir: Path, name: str) -> dict:
    result = run_set(ctx.model, spec, battery, ctx.n, ctx.seed, prepend_bos, ctx.batch_size)
    record = _finish(ctx, result, spec, battery)
    base = artifact.set_stem(spec, battery.name, name, ctx.n, ctx.seed, prepend_bos)
    json_path, _ = artifact.write(record, result, out_dir, base=base)
    _log(json_path, record)
    return record


def summary(record: dict) -> dict:
    """What a verdict reads from a run record, with its reference size (D-014)."""
    r, ref = record["results"], record["reference"]
    ld = r["effect"]["ld"]
    return {"effect_mean": ld["effect_mean"], "sem": ld["sem"], "clean_mean_ld": r["clean"]["mean_ld"],
            "ablated_mean_ld": r["ablated"]["mean_ld"], "ratio_of_means": ld["ratio_of_means"],
            "mean_of_ratios": ld["mean_of_ratios"], "ratio_iqr": ld["ratio_iqr"],
            "value": record["spec"]["value"], "n": record["battery"]["n"],
            "ref_n": None if ref is None else ref["n"],
            "ref_per_template_counts": None if ref is None else ref["per_template_counts"]}


def gap_stats(ctx: Ctx, battery, prepend_bos: bool) -> dict:
    """Clean and corrupt mean ld on the same draw (the E1b gate's measurement),
    and the fraction of the clean ld the scheme removes (D-014 item 2)."""
    cols, templates = e1b_gate.measure(ctx.model, battery, ctx.n, ctx.seed, prepend_bos, ctx.batch_size)
    s = e1b_gate.statistics(cols, templates)
    return {"n": s["n"], "mean_ld_clean": s["clean"]["mean_ld"], "mean_ld_corrupt": s["corrupt"]["mean_ld"],
            "gap": s["gap"], "fraction_removed": s["fraction_removed"]}


def fraction_restored(ablated_mean: float, corrupt_mean: float, gap: float) -> float:
    """Restore-clean on the corrupt prompt: the share of the clean-minus-corrupt
    gap the restored activations recover (1 = all of it)."""
    return (ablated_mean - corrupt_mean) / gap


def below_template_floor(counts: dict[str, int]) -> bool:
    """D-014 item 5's floor of 30 reference prompts per template."""
    return min(counts.values()) < TEMPLATE_FLOOR


def restored_row(unit: str, record: dict, gap: dict) -> dict:
    s = summary(record)
    # Under restore-clean the destination is the corrupt prompt: clean_mean_ld is the
    # corrupt prompt unintervened, ablated_mean_ld the corrupt prompt with clean values restored.
    return {"unit": unit, **s, "fraction_restored": fraction_restored(s["ablated_mean_ld"], s["clean_mean_ld"],
                                                                      gap["gap"])}


def wang_names(hs) -> str:
    return ", ".join(f"{h.layer}.{h.head}" for h in hs)


def grid(t: torch.Tensor) -> dict[str, float]:
    return {label(Head(l, h)): float(t[l, h]) for l in range(t.shape[0]) for h in range(t.shape[1])}


def weights_record(model) -> dict:
    return {"normalization_type": model.cfg.normalization_type,
            "loaded_by": "src/lesion/model.py::load_model (TransformerLens from_pretrained defaults: LayerNorm "
                         "folded, writing weights and unembedding centred)"}


# --- P1 sweeps -----------------------------------------------------------------------------------


def run_sweep(ctx: Ctx, battery, sweep, value: str, prepend_bos: bool, path: Path, candidates=None) -> dict:
    """One edge run per candidate sender, stored as per-sender aggregates (no
    per-prompt parquet). Written atomically. Under ``ctx.resume`` a file is
    reused only if its config and pre-registration status both match."""
    cands = tuple(candidates or sweep.candidates)
    config = {"sweep": sweep.name, "value": value, "n": ctx.n, "seed": ctx.seed, "prepend_bos": prepend_bos,
              "sender_position": sweep.sender_position, "candidates": [label(h) for h in cands],
              "spec_template": edge_spec(cands[0], value, sweep.sender_position, sweep.receiver).to_json()}
    if ctx.resume and path.exists():
        old = json.loads(path.read_text())
        if old["config"] == config and old["pre_registered"] == ctx.pre_registered:
            print(f"  reusing {path}", flush=True)
            return old
    t0 = time.time()
    rows, reference = [], None
    for h in cands:
        res = run(ctx.model, edge_spec(h, value, sweep.sender_position, sweep.receiver), battery, ctx.n, ctx.seed,
                  prepend_bos, ctx.batch_size)
        e = res.aggregates["effect"]["ld"]
        rows.append({"sender": label(h), "effect_mean": e["effect_mean"], "sem": e["sem"],
                     "clean_mean_ld": res.aggregates["clean"]["mean_ld"],
                     "ablated_mean_ld": res.aggregates["ablated"]["mean_ld"], "seconds": res.seconds})
        reference = res.reference_summary
        print(f"  {sweep.name:12} {value:8} {label(h):6} effect {e['effect_mean']:+.4f} ± {e['sem']:.4f}", flush=True)
    record = {"phase": "E2", "command": ctx.command, "pre_registered": ctx.pre_registered, "config": config,
              "battery": e1b_gate.battery_record(battery, ctx.n, ctx.seed, prepend_bos), "reference": reference,
              "effect_sign": "positive = patching the path lowered ld (clean minus intervened, on the clean prompt)",
              "direct_effect_definition": "wang" if isinstance(sweep.receiver, Logits) else None,
              "rows": rows, "environment": artifact.environment_record(ctx.model, ctx.batch_size, time.time() - t0)}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(record, indent=2))
    os.replace(tmp, path)
    return record


def sweep_scores(record: dict) -> dict[str, float]:
    return {r["sender"]: r["effect_mean"] for r in record["rows"]}


def mean_reference_block(record: dict) -> dict:
    """A mean-value sweep record's reference size and per-template counts
    (D-014 items 2, 5), for entries whose ``ungated_beside`` cites a mean run
    without going through ``summary()``."""
    ref = record["reference"]
    return {"n": ref["n"], "per_template_counts": ref["per_template_counts"]}


# --- targets ----------------------------------------------------------------------------------------


def target_i1(ctx: Ctx) -> list[dict]:
    out = ctx.out_dir / "I1"
    out.mkdir(parents=True, exist_ok=True)
    cfg = ctx.model.cfg
    t0 = time.time()
    variants = [("gated", ctx.seed, I1_BOS), ("bos", ctx.seed, True)] + [(f"seed{s}", s, I1_BOS) for s in I1_SPREAD_SEEDS]
    runs = {}
    for name, seed, bos in variants:
        toks = repeated_random_tokens(I1_N_SEQ, I1_HALF_LEN, cfg.d_vocab, seed, ctx.tok.bos_token_id if bos else None)
        start = 1 if bos else 0
        scores = attention_scores(ctx.model, toks, I1_HALF_LEN, start, I1_BATCH)
        scores["copy"] = copy_scores(ctx.model, toks, I1_HALF_LEN, start, I1_BATCH)
        scores["copy_abs"] = scores["copy"].abs()
        runs[name] = {"seed": seed, "prepend_bos": bos, "scores": {k: grid(v) for k, v in scores.items()}}
        print(f"  I1 {name}: done", flush=True)
    gated = runs["gated"]["scores"]
    spread_runs = ["gated"] + [f"seed{s}" for s in I1_SPREAD_SEEDS]
    spread = {k: {h: statistics.stdev(runs[v]["scores"][k][h] for v in spread_runs) for h in gated[k]} for k in gated}
    record = {"phase": "E2", "command": ctx.command, "pre_registered": ctx.pre_registered,
              "stimulus": {"n_sequences": I1_N_SEQ, "half_len": I1_HALF_LEN, "d_vocab": cfg.d_vocab,
                           "sampling": "uniform over every id, with replacement, no exclusions"},
              "definitions": I1_DEFINITIONS, "weights": weights_record(ctx.model), "runs": runs,
              "sd_over_stimulus_seeds_0_4": spread,
              "environment": artifact.environment_record(ctx.model, I1_BATCH, time.time() - t0)}
    (out / "scores.json").write_text(json.dumps(record, indent=2))
    entries = []
    for row in I1_ROWS:
        members = tuple(label(h) for h in row.members)
        res = identity_verdict(gated[row.score], members, row.k, row.bottom)
        beside = {v: identity_verdict(runs[v]["scores"][row.score], members, row.k, row.bottom)["member_ranks"]
                  for v in ["bos", *spread_runs[1:]]}
        if row.score == "copy_abs":
            beside["signed"] = identity_verdict(gated["copy"], members, row.k, row.bottom)["member_ranks"]
        res["ungated_beside"] = beside
        entries.append(entry(row.id, row.source, f"{wang_names(row.members)} in the top {row.stated_rank}",
                             res["member_ranks"], f"top k = {row.k} of {res['n_candidates']}", res))
    return entries


def target_i2(ctx: Ctx) -> list[dict]:
    out = ctx.out_dir / "I2"
    out.mkdir(parents=True, exist_ok=True)
    m = ctx.model
    comp = composition_scores(m.W_Q, m.W_K, m.W_V, m.W_O)
    base = random_baseline(m.cfg.d_model, m.cfg.d_head, I2_BASELINE_DRAWS, I2_BASELINE_SEED)
    L, H = m.cfg.n_layers, m.cfg.n_heads
    cols = {k: [] for k in ("l1", "h1", "l2", "h2", "Q", "K", "V")}
    for l1 in range(L):
        for h1 in range(H):
            for l2 in range(l1 + 1, L):
                for h2 in range(H):
                    for k, v in (("l1", l1), ("h1", h1), ("l2", l2), ("h2", h2)):
                        cols[k].append(v)
                    for mode in "QKV":
                        cols[mode].append(comp[mode][l1, h1, l2, h2].item())
    pq.write_table(pa.table(cols), out / "composition.parquet", compression="zstd", compression_level=9)
    question = {}
    for r in I2_RECEIVERS:
        earlier = [h for h in ALL_HEADS if h.layer < r.layer]
        for mode in "KQV":
            scores = {label(s): comp[mode][s.layer, s.head, r.layer, r.head].item() for s in earlier}
            rk = ranks(scores, bottom=False)
            for s in I2_SENDERS:
                question.setdefault(f"{label(s)}->{label(r)}", {})[mode] = {
                    "score": scores[label(s)], "minus_baseline": scores[label(s)] - base[mode]["mean"],
                    "above_baseline": scores[label(s)] > base[mode]["mean"],
                    "rank_among_earlier": rk[label(s)], "n_earlier": len(earlier)}
    (out / "composition.json").write_text(json.dumps({
        "phase": "E2", "command": ctx.command, "pre_registered": ctx.pre_registered,
        "definition": "evaluators.composition_scores (elhage-2021; row-vector convention; exact norms)",
        "weights": weights_record(m), "baseline": base, "question": question,
        "parquet": "composition.parquet: every (l1, h1, l2, h2) with l2 > l1, raw scores"}, indent=2))
    entries = [entry("I2/composition", "elhage-2021 (scores); O-012 (question)", None,
                     {k: {mode: round(v[mode]["minus_baseline"], 4) for mode in "KQ"} for k, v in question.items()},
                     "measured; score minus the random baseline",
                     {"rule": "measured", "verdict": MEASURED, "question": question, "baseline": base})]
    battery, floor = ioi(ctx), floor_for("ioi")
    context = gap_stats(ctx, battery, IOI_BOS)
    for route in I2_ROUTES:
        for s in I2_SENDERS:
            recs = {v: run_single(ctx, edge_spec(s, v, route.sender_position, route.receiver), battery, IOI_BOS,
                                  out / "path") for v in VALUES}
            g = summary(recs["resample"])
            res = sign_verdict(g["effect_mean"], g["sem"], floor, route.expected)
            res.update({"gated_run": g, "ungated_beside": {v: summary(recs[v]) for v in ("zero", "mean")},
                        "context": context})
            published = "lowers ld (significant)" if route.expected == "positive" else "no significant effect"
            entries.append(entry(f"I2/{route.name}/{label(s)}", route.source, published, g["effect_mean"],
                                 f"|effect| vs max(2 sem, F_ioi = {floor:.4f})", res))
    return entries


def target_i3(ctx: Ctx) -> list[dict]:
    out, battery = ctx.out_dir / "I3", induction(ctx)

    def row(unit: str, value: str, pair: dict) -> dict:
        return {"unit": unit, "value": value, "frozen": pair[True], "unfrozen": pair[False],
                "delta_frozen_minus_unfrozen": pair[True]["effect_mean"] - pair[False]["effect_mean"]}

    table = []
    for h in I3_HEADS:
        for v in VALUES:
            pair = {f: summary(run_single(ctx, node_spec(h, v, All(), freeze=f), battery, INDUCTION_BOS, out))
                    for f in (True, False)}
            table.append(row(label(h), v, pair))
    for v in VALUES:
        pair = {f: summary(run_set_named(ctx, set_spec([Member(h, All()) for h in I3_SET], v, freeze=f), battery,
                                         INDUCTION_BOS, out, "induction_heads")) for f in (True, False)}
        table.append(row("+".join(label(h) for h in I3_SET), v, pair))
    res = {"rule": "measured", "verdict": MEASURED, "table": table, "context": gap_stats(ctx, battery, INDUCTION_BOS),
           "olsson_expectation": "ablating induction heads damages induction: a directional expectation from "
                                 "other models (olsson-2022), not a published GPT-2 small claim"}
    ours = {f"{r['unit']}/zero": round(r["frozen"]["effect_mean"], 4) for r in table if r["value"] == "zero"}
    return [entry("I3/pattern_frozen_ablation", "olsson-2022 (method only; no GPT-2 small number)", None, ours,
                  "measured; frozen with the unfrozen twin beside (O-011)", res)]


def target_i4(ctx: Ctx) -> list[dict]:
    out, battery = ctx.out_dir / "I4", induction(ctx)
    gap = gap_stats(ctx, battery, INDUCTION_BOS)
    rows = [restored_row(f"{label(h)}@{p}", run_single(ctx, node_spec(h, "resample", Labels((p,)),
                                                                        direction="restore-clean"),
                                                         battery, INDUCTION_BOS, out), gap) for h, p in I4_MEMBERS]
    spec = set_spec([Member(h, Labels((p,))) for h, p in I4_MEMBERS], "resample", direction="restore-clean")
    rows.append(restored_row("set of four", run_set_named(ctx, spec, battery, INDUCTION_BOS, out, "induction_circuit"),
                             gap))
    return [entry("I4/restore_clean", "ours (sufficiency direction)", None,
                  {r["unit"]: round(r["fraction_restored"], 4) for r in rows}, "measured; fraction of the gap restored",
                  {"rule": "measured", "verdict": MEASURED, "rows": rows, "context": gap})]


def target_p1(ctx: Ctx) -> list[dict]:
    out, battery, floor = ctx.out_dir / "P1", ioi(ctx), floor_for("ioi")
    recs = {(s.name, v): run_sweep(ctx, battery, s, v, IOI_BOS, out / f"sweep-{s.name}-{v}.json")
            for s in P1_SWEEPS for v in VALUES}
    context = gap_stats(ctx, battery, IOI_BOS)
    entries = []
    for row in P1_ROWS:
        members = tuple(label(h) for h in row.members)
        res = identity_verdict(sweep_scores(recs[(row.score, "resample")]), members, row.k, row.bottom)
        res["ungated_beside"] = {v: identity_verdict(sweep_scores(recs[(row.score, v)]), members, row.k,
                                                     row.bottom)["member_ranks"] for v in ("zero", "mean")}
        if row.score == "sinh_values":
            rk = ranks(sweep_scores(recs[("sinh_values", "resample")]), bottom=False)
            res["fuzzy_ranks"] = {label(h): rk[label(h)] for h in P1_FUZZY}
        res["operationalisation"] = ("ranking by path-patching effect; Wang et al. selected classes from "
                                     "path-patching figures plus follow-up tests")
        res["context"] = context
        res["mean_reference"] = mean_reference_block(recs[(row.score, "mean")])
        res["sweep_files"] = {v: str(out / f"sweep-{row.score}-{v}.json") for v in VALUES}
        side = "bottom" if row.bottom else "top"
        entries.append(entry(row.id, row.source, wang_names(row.members), res["member_ranks"],
                             f"{side} k = {row.k} of {res['n_candidates']}", res))
    for id_, sweep_name, members, expected in P1_SIGN:
        rows = {r["sender"]: r for r in recs[(sweep_name, "resample")]["rows"]}
        per = {label(h): sign_verdict(rows[label(h)]["effect_mean"], rows[label(h)]["sem"], floor, expected)
               for h in members}
        beside = {v: {label(h): sweep_scores(recs[(sweep_name, v)])[label(h)] for h in members} for v in ("zero", "mean")}
        res = {"rule": "sign", "expected": expected, "floor": floor, "members": per, "ungated_beside": beside,
               "context": context, "mean_reference": mean_reference_block(recs[(sweep_name, "mean")]),
               "sweep_files": {v: str(out / f"sweep-{sweep_name}-{v}.json") for v in VALUES},
               "verdict": MATCHED if all(p["verdict"] == MATCHED for p in per.values()) else NOT_MATCHED}
        entries.append(entry(id_, "wang-2022 §3.1, Fig. 3", f"{expected} direct effect for each member",
                             {k: p["effect"] for k, p in per.items()},
                             f"each member: sign and |effect| > max(2 sem, F_ioi = {floor:.4f})", res))
    return entries


def _siblings(ctx: Ctx, out: Path, members, name: str, complement: bool) -> dict:
    """D-006: zero and resample beside the gated mean, once per template mix."""
    sib = {}
    for tpo in sorted({c.templates_per_order for c in CORNERS}, reverse=True):
        battery = ioi(ctx, tpo)
        for v in ("zero", "resample"):
            s = summary(run_set_named(ctx, set_spec(members, v, complement=complement), battery, IOI_BOS,
                                      out / f"t{tpo}-siblings", name))
            sib[f"t{tpo}/{v}"] = s
    return sib


def target_p2(ctx: Ctx) -> list[dict]:
    out, nm = ctx.out_dir / "P2", CLASS["name_mover"]
    members = [Member(h, Labels(("END",))) for h in nm.members]
    quantity, contrast, per_corner, gaps = {}, {}, {}, {}
    for c in CORNERS:
        battery, d = ioi(ctx, c.templates_per_order), out / c.id
        ko = summary(run_set_named(ctx, set_spec(members, "mean", ref_n=c.ref_n), battery, IOI_BOS, d, "name_mover"))
        des = {label(h): summary(run_single(ctx, edge_spec(h, "mean", "END", Logits(), ref_n=c.ref_n), battery,
                                            IOI_BOS, d)) for h in nm.members}
        f_m = ko["clean_mean_ld"]
        quantity[c.id] = ko["effect_mean"] / f_m
        contrast[c.id] = sum(x["effect_mean"] for x in des.values()) / f_m
        per_corner[c.id] = {"knockout": ko, "direct_effects": des, "F_M": f_m,
                            "below_template_floor": below_template_floor(ko["ref_per_template_counts"])}
    for tpo in sorted({c.templates_per_order for c in CORNERS}, reverse=True):
        gaps[f"t{tpo}"] = gap_stats(ctx, ioi(ctx, tpo), IOI_BOS)
    sib = _siblings(ctx, out, members, "name_mover", complement=False)
    for s in sib.values():
        s["quantity"] = s["effect_mean"] / s["clean_mean_ld"]
    res = magnitude_verdict(quantity, P2_PUBLISHED, contrast)
    res.update({"per_corner": per_corner, "ungated_beside": sib, "context": gaps,
                "contrast_definition": "sum of the three single-head direct effects (edge to logits, wang, mean, "
                                       "same corner) over F(M); a sum, not a joint edge ablation"})
    return [entry("P2/nm_knockout_drop", "wang-2022 §3.4, App. F", P2_PUBLISHED, res["bracket"],
                  "bracket over four corners; uninformative if it overlaps the contrast's range", res)]


def target_p3(ctx: Ctx) -> list[dict]:
    out = ctx.out_dir / "P3"
    members = [Member(h, Labels((c.position,))) for c in CLASSES for h in c.members]
    ratio, per_corner, gaps = {}, {}, {}
    for c in CORNERS:
        s = summary(run_set_named(ctx, set_spec(members, "mean", complement=True, ref_n=c.ref_n),
                                  ioi(ctx, c.templates_per_order), IOI_BOS, out / c.id, "circuit"))
        ratio[c.id] = s["ratio_of_means"]
        per_corner[c.id] = {**s, "abs_gap": abs(s["effect_mean"]),
                            "below_template_floor": below_template_floor(s["ref_per_template_counts"])}
    for tpo in sorted({c.templates_per_order for c in CORNERS}, reverse=True):
        gaps[f"t{tpo}"] = gap_stats(ctx, ioi(ctx, tpo), IOI_BOS)
    res = magnitude_verdict(ratio, P3_PUBLISHED, P3_CONTRAST)
    res.update({"per_corner": per_corner, "published_abs_gap": P3_PUBLISHED_ABS_GAP, "granularity": "heads",
                "ungated_beside": _siblings(ctx, out, members, "circuit", complement=True), "context": gaps})
    return [entry("P3/faithfulness", "wang-2022 §4", P3_PUBLISHED, res["bracket"],
                  "bracket over four corners; contrast 1.0", res)]


def target_p4(ctx: Ctx) -> list[dict]:
    out, battery = ctx.out_dir / "P4", ioi(ctx)
    gap = gap_stats(ctx, battery, IOI_BOS)
    rows = []
    for c in CLASSES:
        spec = set_spec([Member(h, Labels((c.position,))) for h in c.members], "resample", direction="restore-clean")
        rows.append(restored_row(f"{c.name}@{c.position}", run_set_named(ctx, spec, battery, IOI_BOS,
                                                                          out / "classes", c.name), gap))
    for c in CLASSES:
        for h in c.members:
            rec = run_single(ctx, node_spec(h, "resample", Labels((c.position,)), direction="restore-clean"),
                             battery, IOI_BOS, out / "heads")
            rows.append(restored_row(f"{label(h)}@{c.position}", rec, gap))
    return [entry("P4/restore_clean", "ours (the sufficiency direction Wang et al. did not run)", None,
                  {r["unit"]: round(r["fraction_restored"], 4) for r in rows[:len(CLASSES)]},
                  "measured; fraction of the gap restored",
                  {"rule": "measured", "verdict": MEASURED, "rows": rows, "context": gap})]


TARGET_FUNCS = {"I1": target_i1, "I2": target_i2, "I3": target_i3, "I4": target_i4,
                "P1": target_p1, "P2": target_p2, "P3": target_p3, "P4": target_p4}
