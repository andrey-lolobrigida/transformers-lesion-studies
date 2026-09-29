"""E2 driver: the pre-registered constants, the verdict rules, and the CLI.

    uv run python -m src.lesion.e2_reproduce --target I1      # one target (I1..I4, P1..P4)
    uv run python -m src.lesion.e2_reproduce --target all     # every target, then the exit table
    uv run python -m src.lesion.e2_reproduce --target table   # rebuild results/E2/verdicts.json
    uv run python -m src.lesion.e2_reproduce --target P1 --resume   # reuse finished (sweep, value) files

Verdicts (D-015): `matched` / `not matched` (identity, sign or magnitude
against a published claim), `bracketed, uninformative` (a magnitude bracket
that contains its contrast value), `measured` (no published GPT-2 small
counterpart). A verdict is written only at the pre-registered n and seed;
every artifact records `pre_registered`. The block below was committed before
the first GPU run, mirrored in results/E2/README.md, and is pinned by
tests/test_e2_reproduce.py. Target code: e2_targets.py."""

from __future__ import annotations

import argparse
import copy
import json
import math
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from src.lesion.spec import Head, Inputs, Logits, Receiver, SpecError


def head(s: str) -> Head:
    """Wang et al.'s "9.6" notation -> Head(9, 6)."""
    layer, h = s.split(".")
    return Head(int(layer), int(h))


def heads(s: str) -> tuple[Head, ...]:
    return tuple(head(x) for x in s.split())


def label(h: Head) -> str:
    return f"L{h.layer}H{h.head}"


ALL_HEADS = tuple(Head(l, h) for l in range(12) for h in range(12))


@dataclass(frozen=True)
class HeadClass:
    name: str
    members: tuple[Head, ...]
    position: str  # the IOI label the class acts at
    source: str


@dataclass(frozen=True)
class IdentityRow:
    id: str
    score: str  # the I1 score or the P1 sweep the class is ranked by
    members: tuple[Head, ...]
    stated_rank: int | None  # the rank the source itself states, if any
    bottom: bool  # negative classes rank from the bottom
    source: str

    @property
    def k(self) -> int:
        """D-015 item 3: never stricter than the source's own claim."""
        return max(len(self.members) + 2, self.stated_rank or len(self.members))


@dataclass(frozen=True)
class Sweep:
    name: str
    sender_position: str
    receiver: Receiver
    source: str

    @property
    def candidates(self) -> tuple[Head, ...]:
        """Senders strictly below every receiver: a path into a head at or
        below the sender's layer is empty, and spec.py refuses it."""
        if isinstance(self.receiver, Logits):
            return ALL_HEADS
        top = min(t[0] for t in self.receiver.targets)
        return tuple(h for h in ALL_HEADS if h.layer < top)


@dataclass(frozen=True)
class Route:
    name: str
    sender_position: str
    receiver: Inputs
    expected: str  # "positive" (the path lowers ld when patched) or "null"
    source: str


@dataclass(frozen=True)
class Corner:
    templates_per_order: int
    ref_n: int

    @property
    def id(self) -> str:
        return f"t{self.templates_per_order}-ref{self.ref_n}"


def check_direct_path(sender_position: str, receiver: Receiver) -> None:
    """A sender reaches a receiver's direct path only through the residual
    stream at the receiver's own position (MLPs and LayerNorms act per
    position). A sender elsewhere gives an effect of exactly zero by
    construction, which would pass a null test trivially: refuse it."""
    wanted = {"END"} if isinstance(receiver, Logits) else {t[3] for t in receiver.targets}
    if wanted != {sender_position}:
        raise SpecError(f"a sender at {sender_position!r} has no direct path to a receiver at {sorted(wanted)}")


# =================================== PRE-REGISTRATION ===================================
# D-015; the E2 spec. Committed before the first GPU run. A change after results
# exist is a new pre-registration and goes to docs/04-decisions.md first.

N, SEED = 2000, 0  # prompts per battery run, and the sample seed
REF_N, REF_SEED = 2000, 0  # mean reference: corrupt side, template-matched (O-015)
VALUES = ("zero", "mean", "resample")  # D-006: the source's value gates, the other two run beside
IOI_BOS, INDUCTION_BOS = False, True  # D-011; the induction battery's default [olsson-2022]
FLOOR_FILES = {"ioi": "results/E1b/noise/ioi/floor.json"}  # F_item for the sign rule: its max_floor

# Wang et al.'s seven classes, 26 heads, each at the position the paper's text gives it.
CLASSES = (
    HeadClass("name_mover", heads("9.6 9.9 10.0"), "END", "wang-2022 §3.1"),
    HeadClass("negative_name_mover", heads("10.7 11.10"), "END",
              "wang-2022 §3.1 (position inferred: 'share all the same properties as Name Mover Heads')"),
    HeadClass("s_inhibition", heads("7.3 7.9 8.6 8.10"), "END", "wang-2022 §3, §3.2"),
    HeadClass("induction", heads("5.5 5.8 5.9 6.9"), "S2", "wang-2022 §3, §3.3; 5.8, 5.9 fuzzy (App. C), classed per App. K"),
    HeadClass("duplicate_token", heads("0.1 0.10 3.0"), "S2", "wang-2022 §3, §3.3; 0.10 fuzzy (App. C), classed per App. K"),
    HeadClass("previous_token", heads("2.2 4.11"), "S1+1", "wang-2022 §3, App. D"),
    HeadClass("backup_name_mover", heads("9.0 9.7 10.1 10.2 10.6 10.10 11.2 11.9"), "END",
              "wang-2022 §3.4, App. F (position inferred: found by the END-position direct-effect sweep)"),
)
CLASS = {c.name: c for c in CLASSES}

# --- I1: evaluator rankings on repeated random tokens [wang-2022 App. H, App. I]
I1_N_SEQ, I1_HALF_LEN = 100, 100  # 100 sequences (ours; Wang gives none) of 100 ids, doubled to AA
I1_BOS = False  # gated: no BOS and no token exclusions (Wang mentions neither)
I1_SPREAD_SEEDS = (1, 2, 3, 4)  # ungated: the spread over stimulus seeds 0-4
I1_DEFINITIONS = {
    "previous_token": "mean over sequences and AA positions j = 1..199 of the attention j -> j-1",
    "induction": "mean over sequences and second-half positions j = 100..199 of the attention j -> j-99",
    "duplicate": "mean over sequences and second-half positions j = 100..199 of the attention j -> j-100",
    "copy": "mean over sequences and positions j = 100..198 of <z_j W_O, W_U[:, x_(j+1)]>; no b_O, no final LayerNorm",
    "copy_abs": "|copy|, the gated ranking: wang-2022 Fig. 17 orders heads by absolute contribution",
    "bos_variant": "every position shifted by one",
}
I1_ROWS = (
    IdentityRow("I1/previous_token", "previous_token", heads("4.11 2.2"), 2, False,
                "wang-2022 App. H: the two heads with the highest previous token score"),
    IdentityRow("I1/induction", "induction", heads("5.5 6.9"), 5, False,
                "wang-2022 App. H: among the 5 heads with the highest induction score"),
    IdentityRow("I1/duplicate", "duplicate", heads("3.0 0.1"), 3, False,
                "wang-2022 App. I: among the three heads with the highest duplicate token score"),
    IdentityRow("I1/copy", "copy_abs", heads("5.5 6.9"), 20, False,
                "wang-2022 App. H, Fig. 17: in the 20 heads contributing the most"),
)

# --- I2: which induction mechanism (O-012) [elhage-2021; wang-2022 App. D]
I2_SENDERS = heads("4.11 2.2")
I2_RECEIVERS = heads("5.5 6.9")
I2_ROUTES = (
    Route("k_route", "S1+1", Inputs(tuple((h.layer, h.head, "k", "S1+1") for h in I2_RECEIVERS)), "positive",
          "wang-2022 App. D, Fig. 13: 4.11 and 2.2 cause a decrease in logit difference through the keys at S1+1"),
    Route("q_route", "S2", Inputs(tuple((h.layer, h.head, "q", "S2") for h in I2_RECEIVERS)), "null",
          "wang-2022 App. D: queries at S2, 'did not find any significant effect'"),
)
I2_BASELINE_DRAWS, I2_BASELINE_SEED = 200, 0

# --- I3: pattern-frozen ablation on induction (verdict: measured) [olsson-2022; O-011]
I3_HEADS = heads("5.5 6.9 4.11 2.2")
I3_SET = heads("5.5 6.9")

# --- I4: restore-clean on induction (verdict: measured)
I4_MEMBERS = ((head("5.5"), "END"), (head("6.9"), "END"), (head("4.11"), "B1"), (head("2.2"), "B1"))

# --- P1: path-patching classes, identity + sign [wang-2022 §3.1-3.3, App. D]
P1_SWEEPS = (
    Sweep("logits", "END", Logits(), "wang-2022 §3.1, Fig. 3"),
    Sweep("nm_queries", "END", Inputs(tuple((h.layer, h.head, "q", "END") for h in CLASS["name_mover"].members)),
          "wang-2022 §3.2, Fig. 4"),
    Sweep("sinh_values", "S2", Inputs(tuple((h.layer, h.head, "v", "S2") for h in CLASS["s_inhibition"].members)),
          "wang-2022 §3.3, Fig. 5"),
    Sweep("ind_keys", "S1+1", Inputs(tuple((h.layer, h.head, "k", "S1+1") for h in I2_RECEIVERS)),
          "wang-2022 App. D, Fig. 13"),
)
P1_ROWS = (
    IdentityRow("P1/name_mover", "logits", heads("9.6 9.9 10.0"), None, False, "wang-2022 §3.1"),
    IdentityRow("P1/negative_name_mover", "logits", heads("10.7 11.10"), None, True, "wang-2022 §3.1"),
    IdentityRow("P1/s_inhibition", "nm_queries", heads("7.3 7.9 8.6 8.10"), None, False, "wang-2022 §3.2"),
    IdentityRow("P1/induction_duplicate", "sinh_values", heads("5.5 6.9 3.0 0.1"), None, False, "wang-2022 §3.3"),
    IdentityRow("P1/previous_token", "ind_keys", heads("4.11 2.2"), None, False, "wang-2022 App. D"),
)
P1_SIGN = (
    ("P1/name_mover/sign", "logits", heads("9.6 9.9 10.0"), "positive"),
    ("P1/negative_name_mover/sign", "logits", heads("10.7 11.10"), "negative"),
)
P1_FUZZY = heads("0.10 5.8 5.9")  # ranks reported, not gated

# --- P2, P3: magnitudes, bracketed over four corners (D-015 item 5)
CORNERS = tuple(Corner(t, r) for t in (15, 7) for r in (7 * 2 * t, 2000))  # ~7 per template, or 2,000 total
P2_PUBLISHED = 0.05  # wang-2022 §3.4, App. F: knocking out the Name Movers, "only 5% drop in logit difference"
P3_PUBLISHED = 0.87  # wang-2022 §4: F(C)/F(M)
P3_PUBLISHED_ABS_GAP = 0.46  # wang-2022 §4: |F(M) - F(C)|, ungated beside
P3_CONTRAST = 1.0  # the circuit does everything the model does

# ================================ END OF PRE-REGISTRATION ================================

TARGETS = ("I1", "I2", "I3", "I4", "P1", "P2", "P3", "P4")
MATCHED, NOT_MATCHED, UNINFORMATIVE, MEASURED = "matched", "not matched", "bracketed, uninformative", "measured"


def ranks(scores: dict[str, float], bottom: bool) -> dict[str, int]:
    """Competition ranks ("1224"): 1 + the number of candidates strictly
    better, so tied candidates share the best rank."""
    bad = sorted(k for k, v in scores.items() if not math.isfinite(v))
    if bad:
        raise ValueError(f"non-finite scores for {bad}")
    return {k: 1 + sum(1 for x in scores.values() if (x < v if bottom else x > v)) for k, v in scores.items()}


def identity_verdict(scores: dict[str, float], members: tuple[str, ...], k: int, bottom: bool) -> dict:
    """D-015 item 3: matched iff every published member ranks in the top
    (or bottom) k. A tie straddling rank k counts as inside and is reported."""
    missing = [m for m in members if m not in scores]
    if missing:
        raise ValueError(f"published members {missing} are not among the {len(scores)} candidates")
    r = ranks(scores, bottom)
    ordered = sorted(scores, key=lambda h: (r[h], h))
    matched = all(r[m] <= k for m in members)
    return {"rule": "identity", "k": k, "bottom": bottom, "n_candidates": len(scores),
            "member_ranks": {m: r[m] for m in members}, "member_scores": {m: scores[m] for m in members},
            "top_k": [[h, scores[h]] for h in ordered[:k]], "tie_at_cut": any(r[h] <= k for h in ordered[k:]),
            "verdict": MATCHED if matched else NOT_MATCHED}


def sign_verdict(effect: float, sem: float, floor: float, expected: str) -> dict:
    """D-015 item 4. ``effect`` is mean(ld unintervened - ld intervened):
    positive when the intervention lowers the logit difference."""
    bad = [name for name, v in (("effect", effect), ("sem", sem), ("floor", floor)) if not math.isfinite(v)]
    if bad:
        raise ValueError(f"non-finite {', '.join(bad)}")
    bound = max(2 * sem, floor)
    if expected == "null":
        ok = abs(effect) <= bound
    elif expected == "positive":
        ok = effect > 0 and abs(effect) > bound
    elif expected == "negative":
        ok = effect < 0 and abs(effect) > bound
    else:
        raise ValueError(f"expected must be positive, negative or null, got {expected!r}")
    return {"rule": "sign", "expected": expected, "effect": effect, "sem": sem, "floor": floor, "bound": bound,
            "bound_source": "2*sem" if 2 * sem >= floor else "floor", "verdict": MATCHED if ok else NOT_MATCHED}


def magnitude_verdict(corners: dict[str, float], published: float, contrast: float | dict[str, float]) -> dict:
    """D-015 item 5. The bracket is [min, max] over the corners. Uninformative
    if it overlaps the contrast (a value, or its range over the corners);
    otherwise matched iff the published value lies inside."""
    cvals = list(contrast.values()) if isinstance(contrast, dict) else [contrast]
    bad = [f"corners[{k!r}]" for k, v in corners.items() if not math.isfinite(v)]
    if not math.isfinite(published):
        bad.append("published")
    if isinstance(contrast, dict):
        bad += [f"contrast[{k!r}]" for k, v in contrast.items() if not math.isfinite(v)]
    elif not math.isfinite(contrast):
        bad.append("contrast")
    if bad:
        raise ValueError(f"non-finite {', '.join(bad)}")
    lo, hi = min(corners.values()), max(corners.values())
    c_lo, c_hi = min(cvals), max(cvals)
    if c_lo <= hi and c_hi >= lo:
        v = UNINFORMATIVE
    elif lo <= published <= hi:
        v = MATCHED
    else:
        v = NOT_MATCHED
    return {"rule": "magnitude", "corners": corners, "bracket": [lo, hi], "width": hi - lo, "published": published,
            "contrast": contrast, "contrast_range": [c_lo, c_hi], "verdict": v}


def floor_for(item: str) -> float:
    """F_item: the item's largest E1b noise floor (ref n 2,000, ref seeds 0-4)."""
    return json.loads(Path(FLOOR_FILES[item]).read_text())["max_floor"]


def is_pre_registered(n: int, seed: int) -> bool:
    return n == N and seed == SEED


def entry(id: str, source: str, published, ours, tolerance: str, result: dict) -> dict:
    """One exit-table row: the published claim, our number, the tolerance, the verdict."""
    return {"id": id, "source": source, "published": published, "ours": ours, "tolerance": tolerance,
            "verdict": result["verdict"], "result": result}


def write_verdicts(out_dir: Path, target: str, entries: list[dict], pre_registered: bool) -> Path:
    entries = copy.deepcopy(entries)
    if not pre_registered:
        for e in entries:
            e["verdict"] = None
            e["withheld"] = f"not at the pre-registered settings (n = {N}, seed = {SEED})"
    d = Path(out_dir) / target
    d.mkdir(parents=True, exist_ok=True)
    path = d / "verdict.json"
    path.write_text(json.dumps({"target": target, "pre_registered": pre_registered, "entries": entries}, indent=2))
    return path


def build_table(out_dir: Path) -> dict:
    """results/E2/verdicts.json: one row per entry, in target order."""
    out_dir = Path(out_dir)
    rows, missing = [], []
    for t in TARGETS:
        p = out_dir / t / "verdict.json"
        if not p.exists():
            missing.append(t)
            continue
        d = json.loads(p.read_text())
        rows += [{"id": e["id"], "published": e["published"], "ours": e["ours"], "tolerance": e["tolerance"],
                  "verdict": e["verdict"], "pre_registered": d["pre_registered"]} for e in d["entries"]]
    counts: dict[str, int] = {}
    for r in rows:
        counts[str(r["verdict"])] = counts.get(str(r["verdict"]), 0) + 1
    table = {"rows": rows, "counts": counts, "missing": missing}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "verdicts.json").write_text(json.dumps(table, indent=2))
    return table


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m src.lesion.e2_reproduce", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", required=True, choices=[*TARGETS, "all", "table"])
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", default="results/E2")
    ap.add_argument("--resume", action="store_true",
                    help="P1: reuse a (sweep, value) file written with the same config and pre-registration status")
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = build_parser()
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    if args.target == "table":
        t = build_table(out)
        print(f"{len(t['rows'])} entries {t['counts']}; missing {t['missing']} -> {out / 'verdicts.json'}")
        return 0
    if args.n <= 0:
        ap.error("--n must be positive")  # exits 2, before any model loads

    from src.lesion import e2_targets
    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(args.seed)
    ctx = e2_targets.Ctx(model=load_model(args.device), tok=plain_tokenizer(), n=args.n, seed=args.seed,
                         batch_size=args.batch_size, out_dir=out,
                         command="uv run python -m src.lesion.e2_reproduce " + " ".join(shlex.quote(a) for a in argv),
                         cli=vars(args), pre_registered=is_pre_registered(args.n, args.seed), resume=args.resume)
    for t in (TARGETS if args.target == "all" else (args.target,)):
        path = write_verdicts(out, t, e2_targets.TARGET_FUNCS[t](ctx), ctx.pre_registered)
        for e in json.loads(path.read_text())["entries"]:
            print(f"{e['id']:32} {str(e['verdict']):26} ours {json.dumps(e['ours'])[:90]}", flush=True)
    if args.target == "all":
        build_table(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
