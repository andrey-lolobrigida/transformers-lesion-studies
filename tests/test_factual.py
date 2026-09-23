"""Factual-recall pairs over a survivor file built from hand-made records."""

import json

import pytest

from src.lesion import counterfact as cf
from src.lesion.factual import LABELS, SUBJECT_SWAP, SUBJECT_SWAP_SYM, FactualBattery
from tests.conftest import make_counterfact


@pytest.fixture
def survivors_file(word_tokenizer, tmp_path):
    records, generate = make_counterfact(word_tokenizer)
    p = tmp_path / "survivors.json"
    p.write_text(json.dumps(cf.build(records, word_tokenizer, generate)))
    return p


def by_case(path):
    return {s["case_id"]: s for s in json.loads(path.read_text())["survivors"]}


def test_fields(word_tokenizer, survivors_file):
    b = FactualBattery(word_tokenizer, path=survivors_file)
    assert b.labels == LABELS == ("SUBJ_FIRST", "SUBJ_LAST", "END")
    assert b.schemes == ("subject_swap", "subject_swap_sym") and b.corruption is SUBJECT_SWAP
    assert FactualBattery(word_tokenizer, "subject_swap_sym", path=survivors_file).corruption is SUBJECT_SWAP_SYM
    assert b.expected_direction == "positive" and b.default_prepend_bos is False
    assert b.n_admitted == 30 and cf.sha256(survivors_file) in b.template_set


def test_pairs_swap_only_the_subject(word_tokenizer, survivors_file):
    b = FactualBattery(word_tokenizer, path=survivors_file)
    recs = by_case(survivors_file)
    admitted_keys = {"The capital of {} is|s1|g"}
    for pr in b.pairs(30, seed=0, prepend_bos=False):
        me, partner_o = recs[int(pr.meta["case_id"])], int(pr.meta["partner_o_id"])
        p = pr.positions
        assert pr.template in admitted_keys and p == pr.corrupt_positions
        assert len(pr.clean_ids) == len(pr.corrupt_ids) and p["END"] == len(pr.clean_ids) - 1
        span = range(p["SUBJ_FIRST"], p["SUBJ_LAST"] + 1)
        assert list(pr.clean_ids[span.start:span.stop]) == me["subject_ids"]
        assert pr.clean_ids[span.start:span.stop] != pr.corrupt_ids[span.start:span.stop]
        for i, (a, c) in enumerate(zip(pr.clean_ids, pr.corrupt_ids)):
            if i not in span:
                assert a == c
        assert (pr.answer_id, pr.competitor_id) == (me["o_id"], me["new_id"])
        assert partner_o not in (me["o_id"], me["new_id"])


def test_suffix_kept_verbatim(word_tokenizer, survivors_file):
    d = json.loads(survivors_file.read_text())
    for v in d["templates"].values():
        v["admitted"] = True
    survivors_file.write_text(json.dumps(d))
    b = FactualBattery(word_tokenizer, path=survivors_file)
    (pr,) = [x for x in b.pairs(b.n_admitted, seed=0, prepend_bos=False) if x.meta["case_id"] == "1"]
    suffix = tuple(by_case(survivors_file)[1]["suffix_ids"])
    assert suffix and pr.clean_ids[-len(suffix):] == pr.corrupt_ids[-len(suffix):] == suffix


def test_sym_uses_the_partners_object_and_the_same_partner(word_tokenizer, survivors_file):
    a = FactualBattery(word_tokenizer, "subject_swap", path=survivors_file).pairs(30, seed=2, prepend_bos=False)
    s = FactualBattery(word_tokenizer, "subject_swap_sym", path=survivors_file).pairs(30, seed=2, prepend_bos=False)
    for x, y in zip(a, s):
        assert x.clean_ids == y.clean_ids and x.corrupt_ids == y.corrupt_ids
        assert x.meta["partner_case_id"] == y.meta["partner_case_id"]
        assert y.competitor_id == int(y.meta["partner_o_id"]) != y.answer_id


def test_pairs_refuses_more_than_admitted(word_tokenizer, survivors_file):
    with pytest.raises(ValueError, match="30 admitted"):
        FactualBattery(word_tokenizer, path=survivors_file).pairs(31, seed=0, prepend_bos=False)


def test_seeded_and_bos(word_tokenizer, survivors_file):
    b = FactualBattery(word_tokenizer, path=survivors_file)
    assert b.pairs(10, seed=1, prepend_bos=False) == b.pairs(10, seed=1, prepend_bos=False)
    bos = word_tokenizer.bos_token_id
    for x, y in zip(b.pairs(10, seed=1, prepend_bos=False), b.pairs(10, seed=1, prepend_bos=True)):
        assert y.clean_ids == (bos, *x.clean_ids) and y.corrupt_ids == (bos, *x.corrupt_ids)
        assert y.positions == {k: v + 1 for k, v in x.positions.items()}


def test_preflight_names_the_build_command(tmp_path):
    with pytest.raises(ValueError, match="src.lesion.counterfact"):
        FactualBattery.preflight(tmp_path / "missing.json")
