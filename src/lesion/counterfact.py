"""CounterFact [meng-2022] -> the factual-recall survivor file.

    uv run python -m src.lesion.counterfact              # download (hash-checked), filter, write
    uv run python -m src.lesion.counterfact --device cpu

Per record, the main rewrite prompt only. Filters, in order, each counted:
1. ``" " + target_true`` and ``" " + target_new`` are each one GPT-2 token.
2. The prompt tokenises as three segments (prefix, subject, rest) whose
   concatenation equals the whole prompt's tokenisation (ours: lets the
   subject be swapped by id without re-encoding).
3. Known-facts filter, copied from ROME [meng-2022 App. B.1] and re-run on
   GPT-2 small: greedy generation from the prompt; keep if it names ``o``
   before any other capitalised word; the prompt becomes the text up to but
   not including ``o``. Ours: 10 generated tokens; "names o" means the single
   token ``" " + target_true`` is generated; no BOS (factual's default).
4. At least one eligible subject-swap partner (``eligible_partners``).
Then templates, keyed by (prompt template, subject token length, generated
suffix ids), are admitted only with >= TEMPLATE_FLOOR survivors.

The raw file is not committed (``.cache/`` is gitignored); URL and SHA-256 are
pinned here, and a hash mismatch is a hard stop. The survivor file carries the
partner pool so the battery (``factual.py``) runs offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import time
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.lesion.battery import TEMPLATE_FLOOR, encode

URL = "https://rome.baulab.info/data/dsets/counterfact.json"
# Confirmed 2026-09-23: 45,108,470 bytes, 21,919 records.
SHA256 = "d017056125178a13728594e66a801357a8db9ed7973a7425554bb4271de9fc6f"
RAW = Path(".cache/counterfact/counterfact.json")
SURVIVORS = Path("batteries/factual/survivors.json")
MAX_NEW_TOKENS = 10


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(path=RAW, url: str = URL, expected: str = SHA256) -> Path:
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(path)
    got = sha256(path)
    if got != expected:
        raise ValueError(f"{path}: sha256 {got}, expected {expected} (CounterFact changed or the download is corrupt)")
    return path


@dataclass(frozen=True)
class Segmented:
    prefix_ids: tuple[int, ...]
    subject_ids: tuple[int, ...]
    rest_ids: tuple[int, ...]


def segment(tokenizer, template: str, subject: str) -> Segmented | None:
    """Prefix / subject / rest token ids, the subject carrying the template's
    space before it. None when the pieces do not tokenise like the whole."""
    k = template.index("{}")
    prefix, rest = template[:k], template[k + 2:]
    subject_text = subject
    if prefix.endswith(" "):
        prefix, subject_text = prefix[:-1], " " + subject
    pieces = [encode(tokenizer, t) if t else [] for t in (prefix, subject_text, rest)]
    if not pieces[1] or pieces[0] + pieces[1] + pieces[2] != encode(tokenizer, template.replace("{}", subject)):
        return None
    return Segmented(*(tuple(p) for p in pieces))


def single_token(tokenizer, word: str) -> int | None:
    ids = encode(tokenizer, " " + word)
    return ids[0] if len(ids) == 1 else None


def known_fact_suffix(generated: list[int], o_id: int, decode) -> list[int] | None:
    """ROME's known-facts rule on one generation: the ids generated before
    ``o`` if ``o`` comes before any other capitalised word, else None."""
    for k, t in enumerate(generated):
        if t == o_id:
            return list(generated[:k])
        if decode([t]).strip()[:1].isupper():
            return None
    return None


def greedy(model, prompts: list[list[int]], max_new: int, batch_size: int) -> list[list[int]]:
    """Greedy argmax continuation, batched by prompt length (no padding)."""
    import torch

    from src.lesion.runner import group_by_length

    out: list[list[int]] = [[] for _ in prompts]
    with torch.no_grad():
        for batch in group_by_length(prompts, batch_size):
            toks = torch.tensor([prompts[i] for i in batch], device=model.cfg.device)
            steps = []
            for _ in range(max_new):
                nxt = model(toks)[:, -1, :].argmax(-1)
                steps.append(nxt)
                toks = torch.cat([toks, nxt[:, None]], dim=1)
            gen = torch.stack(steps, dim=1).tolist()
            for j, i in enumerate(batch):
                out[i] = gen[j]
    return out


def template_key(template: str, subject_len: int, suffix: list[int]) -> str:
    return f"{template}|s{subject_len}|g{'.'.join(str(t) for t in suffix)}"


def partner_key(template: str, subject_len: int) -> str:
    return f"{template}|s{subject_len}"


def eligible_partners(survivor: dict, group: list[dict]) -> list[dict]:
    """Subject-swap partners: same partner_key group, another record, another
    subject, and a true object that is neither ``o`` nor ``target_new``."""
    return [q for q in group
            if q["case_id"] != survivor["case_id"] and list(q["subject_ids"]) != list(survivor["subject_ids"])
            and q["o_id"] not in (survivor["o_id"], survivor["new_id"])]


def build(records: list[dict], tokenizer, generate) -> dict:
    """Filters, partner pool and template admission. ``generate`` maps a list
    of prompt id lists to a list of generated id lists (the model, in the CLI)."""
    counts = defaultdict(int)
    counts["records"] = len(records)
    pool = []
    for r in records:
        rr = r["requested_rewrite"]
        o_id, new_id = single_token(tokenizer, rr["target_true"]["str"]), single_token(tokenizer, rr["target_new"]["str"])
        if o_id is None or new_id is None:
            counts["multi_token_target"] += 1
            continue
        seg = segment(tokenizer, rr["prompt"], rr["subject"])
        if seg is None:
            counts["segment_misaligned"] += 1
            continue
        pool.append({
            "case_id": r["case_id"], "relation_id": rr["relation_id"], "template": rr["prompt"],
            "subject": rr["subject"], "prefix_ids": list(seg.prefix_ids), "subject_ids": list(seg.subject_ids),
            "rest_ids": list(seg.rest_ids), "o_id": o_id, "o_str": rr["target_true"]["str"],
            "new_id": new_id, "new_str": rr["target_new"]["str"],
            "partner_key": partner_key(rr["prompt"], len(seg.subject_ids)),
        })
    counts["pool"] = len(pool)

    partners: dict[str, list[dict]] = defaultdict(list)
    for p in pool:
        partners[p["partner_key"]].append({"case_id": p["case_id"], "subject": p["subject"],
                                           "subject_ids": p["subject_ids"], "o_id": p["o_id"], "o_str": p["o_str"]})

    generations = generate([p["prefix_ids"] + p["subject_ids"] + p["rest_ids"] for p in pool])
    decode = tokenizer.decode
    survivors = []
    for p, gen in zip(pool, generations):
        suffix = known_fact_suffix(gen, p["o_id"], decode)
        if suffix is None:
            counts["not_known"] += 1
            continue
        if not eligible_partners(p, partners[p["partner_key"]]):
            counts["no_partner"] += 1
            continue
        survivors.append({**p, "suffix_ids": suffix,
                          "template_key": template_key(p["template"], len(p["subject_ids"]), suffix)})
    counts["known_with_partner"] = len(survivors)

    sizes: dict[str, int] = defaultdict(int)
    for s in survivors:
        sizes[s["template_key"]] += 1
    templates = {k: {"n": n, "admitted": n >= TEMPLATE_FLOOR} for k, n in sorted(sizes.items())}
    counts["templates"] = len(templates)
    counts["admitted_templates"] = sum(v["admitted"] for v in templates.values())
    counts["admitted"] = sum(v["n"] for v in templates.values() if v["admitted"])
    order = ("records", "multi_token_target", "segment_misaligned", "pool", "not_known", "no_partner",
             "known_with_partner", "templates", "admitted_templates", "admitted")
    return {"counts": {k: counts[k] for k in order}, "template_floor": TEMPLATE_FLOOR,
            "templates": templates, "survivors": survivors, "partners": dict(partners)}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="python -m src.lesion.counterfact", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--out", default=str(SURVIVORS))
    args = ap.parse_args(argv)

    from src.lesion import artifact
    from src.lesion.model import load_model, plain_tokenizer, set_determinism

    set_determinism(0)
    raw = download()
    records = json.loads(raw.read_text())
    tok = plain_tokenizer()
    model = load_model(args.device)
    t0 = time.time()
    out = build(records, tok, lambda ps: greedy(model, ps, MAX_NEW_TOKENS, args.batch_size))
    record = {
        "phase": "E1b",
        "command": "uv run python -m src.lesion.counterfact " + " ".join(shlex.quote(a) for a in argv),
        "source": {"url": URL, "sha256": SHA256, "records": len(records), "citation": "meng-2022"},
        "filter": {"rule": "ROME known-facts filter [meng-2022 App. B.1], re-run on GPT-2 small",
                   "max_new_tokens": MAX_NEW_TOKENS, "prepend_bos": False, "decoding": "greedy argmax",
                   "seed": "none (greedy is deterministic)"},
        "environment": artifact.environment_record(model, args.batch_size, time.time() - t0),
        **out,
    }
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, separators=(",", ":")))
    print(json.dumps(out["counts"], indent=2))
    print(f"-> {path} ({path.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
