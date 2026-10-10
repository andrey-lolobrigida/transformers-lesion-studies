"""E3 selection (D-016 items 3-4): the main Holm family over the selecting
draw, rule A per cell set, and the check of the author's exploratory list.

    uv run python -m src.lesion.e3_select --stage confirmatory
        # -> results/E3/selection/tests.json (5,616 tests) and confirmatory.json
    uv run python -m src.lesion.e3_select --stage exploratory
        # checks results/E3/selection/exploratory.json, written by the author after looking at the maps

The family: every total-effect cell (2,808), every direct-effect cell
(1,404), every frozen delta (1,404; frozen effect minus unfrozen effect, per
component, item and value). A delta whose per-prompt differences are all
exactly zero (and, for mean, whose delta is zero at every reference seed) is
exact by construction: expected for layer-11 components, which have no
attention layer downstream for freezing to act on. It is recorded as
`exact_zero`, not tested, and kept in the family with p = 1, so m stays
5,616; this can only make Holm stricter. Any other s = 0 is a hard stop.

confirmatory.json is committed before any verification run, exploratory.json
before its own; e3_verify refuses an uncommitted list (``load_list``).

Both files carry, beside the command, the code revision that wrote them
(src/lesion/ must be committed), the prompt and reference seeds, the model
revision of the input records, and the code revisions of the input cells."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from src.lesion.e3_prereg import (
    ALPHA, COMPONENTS, ITEM, K, MAP, MAPS, N_FAMILY, REF_SEEDS, SEED, VALUES, label, parse_label,
)
from src.lesion.e3_stats import cell_s, holm, paired_sem, select_rule_a, z_test
from src.lesion.e3_sweep import CellSet, check_writable, load_prompts, load_record, one_model_revision, stage_dir

LISTS = ("confirmatory", "exploratory")


class SelectionError(ValueError):
    """The selection inputs are missing, incomplete, or malformed."""


class _Records:
    """Complete, pre-registered cell-set records, read once each."""

    def __init__(self, root: Path) -> None:
        self.root, self.cache = Path(root), {}

    def get(self, item: str, map_id: str, ref_seed: int | None) -> dict:
        stage = "floor" if ref_seed not in (None, REF_SEEDS[0]) else "selection"
        key = (item, map_id, ref_seed)
        if key not in self.cache:
            path = stage_dir(self.root, stage, item) / f"{CellSet(item, map_id, SEED, ref_seed).stem}.json"
            if not path.exists():
                raise SelectionError(f"{path} missing: run `uv run python -m src.lesion.e3_sweep --stage {stage}`")
            rec = load_record(path)
            if not rec["complete"]:
                raise SelectionError(f"{path} is incomplete ({len(rec['components'])}/{len(COMPONENTS)} cells)")
            if not rec["pre_registered"]:
                raise SelectionError(f"{path} was not written at the pre-registered n and batch size")
            self.cache[key] = rec
        return self.cache[key]

    def effects_over_ref_seeds(self, item: str, map_id: str, lab: str) -> list[float]:
        return [self.get(item, map_id, rs)["cells"][lab]["effect_mean"] for rs in REF_SEEDS]

    def prompts(self, item: str, map_id: str, ref_seed: int | None) -> dict:
        return load_prompts(stage_dir(self.root, "selection", item)
                            / f"{CellSet(item, map_id, SEED, ref_seed).stem}.parquet")


def _test(item: str, map_id: str, kind: str, lab: str, value: str, effect: float, s: dict) -> dict:
    return {"id": f"{item}/{map_id}/{lab}", "kind": kind, "item": item, "map": map_id, "component": lab,
            "value": value, "effect": effect, **s, **z_test(effect, s["s"]), "tested": True}


def build_tests(root, recs: _Records | None = None) -> list[dict]:
    recs = recs or _Records(Path(root))
    tests: list[dict] = []
    for item in ITEM:
        for m in MAPS:
            rec = recs.get(item, m.id, REF_SEEDS[0] if m.value == "mean" else None)
            for c in COMPONENTS:
                lab = label(c)
                cell = rec["cells"][lab]
                ref = recs.effects_over_ref_seeds(item, m.id, lab) if m.value == "mean" else None
                tests.append(_test(item, m.id, m.kind, lab, m.value, cell["effect_mean"], cell_s(cell["sem"], ref)))
        for v in VALUES:
            un_id, fr_id = f"total_{v}_unfrozen", f"total_{v}_frozen"
            rs0 = REF_SEEDS[0] if v == "mean" else None
            un, fr = recs.get(item, un_id, rs0), recs.get(item, fr_id, rs0)
            un_p, fr_p = recs.prompts(item, un_id, rs0), recs.prompts(item, fr_id, rs0)
            for c in COMPONENTS:
                lab = label(c)
                delta = fr["cells"][lab]["effect_mean"] - un["cells"][lab]["effect_mean"]
                psem = paired_sem(fr_p[lab]["ld_ablated"], un_p[lab]["ld_ablated"])
                ref = None
                if v == "mean":
                    ref = [f - u for f, u in zip(recs.effects_over_ref_seeds(item, fr_id, lab),
                                                 recs.effects_over_ref_seeds(item, un_id, lab))]
                if psem == 0.0 and delta == 0.0 and (ref is None or all(x == 0.0 for x in ref)):
                    tests.append({"id": f"{item}/delta_{v}/{lab}", "kind": "delta", "item": item,
                                  "map": f"delta_{v}", "component": lab, "value": v, "effect": 0.0, "s": 0.0,
                                  "sem": 0.0, "ref_sd": None if ref is None else 0.0, "source": "exact_zero",
                                  "z": None, "p": 1.0, "tested": False})
                    continue
                tests.append(_test(item, f"delta_{v}", "delta", lab, v, delta, cell_s(psem, ref)))
    if len(tests) != N_FAMILY:
        raise SelectionError(f"family has {len(tests)} tests, pre-registered {N_FAMILY}")
    h = holm({t["id"]: t["p"] for t in tests}, ALPHA)
    for t in tests:
        t.update(holm_step=h[t["id"]]["step"], holm_threshold=h[t["id"]]["threshold"], reject=h[t["id"]]["reject"])
    return tests


def provenance(recs: _Records) -> dict:
    """Rule 6 for a record derived from the cell sets ``recs`` has read: seeds, model revision, input code revisions."""
    try:
        model_revision = one_model_revision(recs.cache.values(), "selection")
    except ValueError as e:
        raise SelectionError(str(e)) from e
    return {"prompt_seed": SEED, "ref_seeds": list(REF_SEEDS), "model_revision": model_revision,
            "input_code_revs": sorted({c["code_rev"] for r in recs.cache.values() for c in r["cells"].values()})}


def select(tests: list[dict]) -> dict:
    by_id = {t["id"]: t for t in tests}
    sets, selections = {}, []
    for item in ITEM:
        for m in MAPS:
            key = f"{item}/{m.id}"
            res = select_rule_a({t["component"]: {"effect": t["effect"], "reject": t["reject"]}
                                 for t in tests if t["item"] == item and t["map"] == m.id}, K)
            sets[key] = res
            for x in res["selected"]:
                t = by_id[f"{key}/{x['component']}"]
                selections.append({"id": t["id"], "item": item, "map": m.id, "component": x["component"],
                                   "rank": x["rank"], "effect": t["effect"], "s": t["s"], "z": t["z"], "p": t["p"]})
    return {"rule": "A", "k": K, "alpha": ALPHA, "n_tests": len(tests), "sets": sets, "selections": selections}


def check_exploratory(entries: list[dict], confirmatory: dict, tests_by_id: dict) -> list[dict]:
    """Each entry names the cell set it is verified under: {item, map, component, why}."""
    confirmed = {s["id"] for s in confirmatory["selections"]}
    seen: set[str] = set()
    out = []
    for e in entries:
        if set(e) != {"item", "map", "component", "why"}:
            raise SelectionError(f"entry {e}: needs exactly item, map, component, why")
        if e["item"] not in ITEM or e["map"] not in MAP:
            raise SelectionError(f"entry {e}: unknown item or map (maps: {list(MAP)})")
        try:
            known = parse_label(e["component"]) in COMPONENTS
        except ValueError:
            known = False
        if not known:
            raise SelectionError(f"entry {e}: unknown component")
        if not str(e["why"]).strip():
            raise SelectionError(f"entry {e}: 'why' must say why it was picked")
        id_ = f"{e['item']}/{e['map']}/{e['component']}"
        if id_ in seen:
            raise SelectionError(f"duplicate entry {id_}")
        if id_ in confirmed:
            raise SelectionError(f"{id_} is already a confirmatory selection")
        seen.add(id_)
        t = tests_by_id[id_]
        rank = confirmatory["sets"][f"{e['item']}/{e['map']}"]["ranks"].get(e["component"])
        out.append({"id": id_, "item": e["item"], "map": e["map"], "component": e["component"], "why": e["why"],
                    "rank": rank, "effect": t["effect"], "s": t["s"], "z": t["z"], "p": t["p"],
                    "reject": t["reject"]})
    return out


def require_committed(path, cwd=None) -> None:
    """A list counts as committed when git tracks it and it has no uncommitted change."""
    p = str(path)
    if subprocess.run(["git", "ls-files", "--error-unmatch", p], cwd=cwd, capture_output=True).returncode != 0:
        raise SelectionError(f"{p} is not committed: commit it before any verification run")
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", p], cwd=cwd).returncode != 0:
        raise SelectionError(f"{p} has uncommitted changes")


def load_list(root, name: str) -> list[dict]:
    """The selections a verification run uses. Refuses an uncommitted list."""
    sel = Path(root) / "selection"
    if name not in LISTS:
        raise SelectionError(f"list must be one of {LISTS}")
    require_committed(sel / "confirmatory.json")
    confirmatory = json.loads((sel / "confirmatory.json").read_text())
    if name == "confirmatory":
        return confirmatory["selections"]
    require_committed(sel / "exploratory.json")
    tests = {t["id"]: t for t in json.loads((sel / "tests.json").read_text())["tests"]}
    return check_exploratory(json.loads((sel / "exploratory.json").read_text())["entries"], confirmatory, tests)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e3_select", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=LISTS)
    ap.add_argument("--out-root", default="results/E3")
    args = ap.parse_args(argv)
    sel = Path(args.out_root) / "selection"
    command = "uv run python -m src.lesion.e3_select " + " ".join(shlex.quote(a) for a in argv)
    try:
        if args.stage == "confirmatory":
            stamp = {"phase": "E3", "command": command, "code_rev": check_writable(args.out_root, allow_dirty=False)}
            recs = _Records(Path(args.out_root))
            tests = build_tests(args.out_root, recs)
            stamp.update(provenance(recs))
            conf = select(tests)
            sel.mkdir(parents=True, exist_ok=True)
            (sel / "tests.json").write_text(json.dumps(
                {**stamp, "family": "main", "alpha": ALPHA, "n_tests": len(tests),
                 "n_rejected": sum(t["reject"] for t in tests), "n_exact_zero": sum(not t["tested"] for t in tests),
                 "tests": tests}, indent=2))
            (sel / "confirmatory.json").write_text(json.dumps({**stamp, **conf}, indent=2))
            for key, res in conf["sets"].items():
                print(f"{key:36} cleared {res['n_cleared']:3}  selected {len(res['selected']):2}"
                      f"{'  (tie at cut)' if res['tie_at_cut'] else ''}")
            print(f"{len(conf['selections'])} confirmatory selections -> {sel / 'confirmatory.json'}")
        else:
            path = sel / "exploratory.json"
            if not path.exists():
                raise SelectionError(f"{path} missing: the author writes it (it may hold an empty 'entries' list)")
            confirmatory = json.loads((sel / "confirmatory.json").read_text())
            tests = {t["id"]: t for t in json.loads((sel / "tests.json").read_text())["tests"]}
            out = check_exploratory(json.loads(path.read_text())["entries"], confirmatory, tests)
            print(f"{len(out)} exploratory entries, well-formed")
    except ValueError as e:  # SelectionError, or check_writable's refusal
        ap.error(str(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
