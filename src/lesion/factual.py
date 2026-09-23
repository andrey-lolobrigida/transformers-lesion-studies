"""Factual recall over CounterFact survivors [meng-2022], built by
``python -m src.lesion.counterfact`` into ``batteries/factual/survivors.json``.

Clean: prefix + subject + rest + generated suffix, all stored token ids, read
at the last token. ``c = " " + target_true``. Default corruption
``subject_swap``: the subject replaced by a partner's subject (same template,
same subject token length, true object neither ``o`` nor ``target_new``);
``s = " " + target_new``. Extra ``subject_swap_sym``: the same swap with
``s = o'``, the partner's object. ROME's Gaussian embedding noise is deferred
(it needs an intervention in ``interventions.py``; D-014 item 6).

Metric: ``ld``, with ``P[o]`` reported beside it (the O-009 addendum: ROME's
metric is a probability; ours is a translation until the two are shown to agree)."""

from __future__ import annotations

import json
import random
from pathlib import Path

from src.lesion import counterfact as cf
from src.lesion.battery import TEMPLATE_FLOOR, Corruption, PromptPair, resolve_scheme, with_bos

SURVIVORS = cf.SURVIVORS
LABELS = ("SUBJ_FIRST", "SUBJ_LAST", "END")

_SOURCE = "meng-2022 (CounterFact; known-facts filter App. B.1); subject swap ours (D-014 item 6)"
_REMOVES = ("the subject, hence the fact: the clean subject is replaced by another CounterFact subject with the "
            "same prompt template and the same subject token length")
SUBJECT_SWAP = Corruption(
    name="subject_swap", removes=_REMOVES,
    inserts="a different subject of the same relation whose own true object is neither c (the clean object) nor "
            "s (the clean record's target_new); template, prefix, rest and the clean generated suffix kept "
            "verbatim. Expected corrupt ld near 0 up to any prior preference between o and target_new. Under "
            "resample ablation the corrupt prompt injects its own object, which is neither c nor s",
    source=_SOURCE)
SUBJECT_SWAP_SYM = Corruption(
    name="subject_swap_sym", removes=_REMOVES,
    inserts="the same partner subject as subject_swap, with the competitor s set to the partner's own true "
            "object o': the corrupt prompt favours s, so the corrupt ld goes negative (the Sports Players case, "
            "miller-2024 App. D.2)",
    source=_SOURCE + "; symmetric competitor after miller-2024 App. D.2")
SCHEMES = {"subject_swap": SUBJECT_SWAP, "subject_swap_sym": SUBJECT_SWAP_SYM}


class FactualBattery:
    """CounterFact survivors, corrupt by subject swap. Implements ``battery.Battery``."""

    name = "factual"
    labels = LABELS
    schemes = ("subject_swap", "subject_swap_sym")
    expected_direction = "positive"
    default_prepend_bos = False  # ROME's prompts are plain text; the filter ran without BOS

    @classmethod
    def preflight(cls, path=None) -> None:
        path = Path(SURVIVORS if path is None else path)
        if not path.exists():
            raise ValueError(f"{path} missing: build it with `uv run python -m src.lesion.counterfact`")

    def __init__(self, tokenizer, scheme: str | None = None, path=None) -> None:
        path = Path(SURVIVORS if path is None else path)
        self.preflight(path)
        self.bos_id = tokenizer.bos_token_id
        self.scheme = resolve_scheme(self.schemes, scheme)
        self.corruption = SCHEMES[self.scheme]
        data = json.loads(path.read_text())
        admitted_keys = {k for k, v in data["templates"].items() if v["admitted"]}
        self.admitted = [s for s in data["survivors"] if s["template_key"] in admitted_keys]
        self.n_admitted = len(self.admitted)
        self.partners = data["partners"]
        self.template_set = (f"CounterFact main rewrite prompts, single-token targets, ROME known-facts filter "
                             f"re-run on GPT-2 small; {self.n_admitted} survivors in {len(admitted_keys)} admitted "
                             f"templates (>= {TEMPLATE_FLOOR} each); {path} sha256 {cf.sha256(path)}")

    def pairs(self, n: int, seed: int, prepend_bos: bool) -> list[PromptPair]:
        if n > self.n_admitted:
            raise ValueError(f"asked for {n} factual pairs; only {self.n_admitted} admitted survivors exist")
        chosen = random.Random(seed).sample(self.admitted, n)
        prng = random.Random(f"subject_swap/{seed}")  # both schemes draw the same partner
        out = []
        for s in chosen:
            q = prng.choice(cf.eligible_partners(s, self.partners[s["partner_key"]]))
            head, tail = s["prefix_ids"], s["rest_ids"] + s["suffix_ids"]
            clean, corrupt = head + s["subject_ids"] + tail, head + q["subject_ids"] + tail
            pos = {"SUBJ_FIRST": len(head), "SUBJ_LAST": len(head) + len(s["subject_ids"]) - 1,
                   "END": len(clean) - 1}
            cpos = dict(pos)
            if prepend_bos:
                clean, pos = with_bos(clean, pos, self.bos_id)
                corrupt, cpos = with_bos(corrupt, cpos, self.bos_id)
            competitor = s["new_id"] if self.scheme == "subject_swap" else q["o_id"]
            out.append(PromptPair(
                clean_ids=tuple(clean), corrupt_ids=tuple(corrupt), answer_id=s["o_id"], competitor_id=competitor,
                positions=pos, corrupt_positions=cpos, template=s["template_key"],
                meta={"case_id": str(s["case_id"]), "partner_case_id": str(q["case_id"]), "subject": s["subject"],
                      "partner_subject": q["subject"], "partner_o_id": str(q["o_id"])},
            ))
        return out
