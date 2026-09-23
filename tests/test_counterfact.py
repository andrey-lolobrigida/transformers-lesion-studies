"""CounterFact filters and the survivor-file builder. Offline: hand-built
records, the word tokenizer, a fake generator; greedy() on the tiny model."""

import hashlib

import pytest
import torch

from src.lesion import counterfact as cf
from src.lesion.battery import encode
from tests.conftest import make_counterfact


def test_pinned_source():
    assert cf.URL == "https://rome.baulab.info/data/dsets/counterfact.json"
    assert cf.SHA256 == "d017056125178a13728594e66a801357a8db9ed7973a7425554bb4271de9fc6f"
    assert cf.MAX_NEW_TOKENS == 10


def test_download_checks_the_hash(tmp_path, monkeypatch):
    def fake_retrieve(url, dest):
        open(dest, "wb").write(b"hello")

    monkeypatch.setattr(cf.urllib.request, "urlretrieve", fake_retrieve)
    good = hashlib.sha256(b"hello").hexdigest()
    p = cf.download(tmp_path / "a.json", url="x", expected=good)
    assert p.read_bytes() == b"hello" and cf.sha256(p) == good
    with pytest.raises(ValueError, match="sha256"):
        cf.download(tmp_path / "b.json", url="x", expected="0" * 64)


def test_segment_with_space_before_subject(word_tokenizer):
    seg = cf.segment(word_tokenizer, "The mother tongue of {} is", "Danielle Darrieux")
    assert seg.prefix_ids == tuple(encode(word_tokenizer, "The mother tongue of"))
    assert seg.subject_ids == tuple(encode(word_tokenizer, " Danielle Darrieux")) and len(seg.subject_ids) == 2
    assert seg.rest_ids == tuple(encode(word_tokenizer, " is"))


def test_segment_subject_first(word_tokenizer):
    seg = cf.segment(word_tokenizer, "{} is a citizen of", "Toko Yasuda")
    assert seg.prefix_ids == () and seg.subject_ids == tuple(encode(word_tokenizer, "Toko Yasuda"))


def test_segment_refuses_misalignment(word_tokenizer):
    assert cf.segment(word_tokenizer, "x{}y", "Foo") is None  # pieces tokenise differently from the whole


def test_single_token(word_tokenizer):
    assert cf.single_token(word_tokenizer, "Paris") == encode(word_tokenizer, " Paris")[0]
    assert cf.single_token(word_tokenizer, "New York") is None


def test_known_fact_suffix():
    words = {1: " the", 2: " city", 3: " Paris", 4: " London", 5: ","}

    def dec(ids):
        return "".join(words[i] for i in ids)

    assert cf.known_fact_suffix([3, 5], o_id=3, decode=dec) == []
    assert cf.known_fact_suffix([1, 2, 3], o_id=3, decode=dec) == [1, 2]
    assert cf.known_fact_suffix([1, 4, 3], o_id=3, decode=dec) is None  # another capitalised word first
    assert cf.known_fact_suffix([1, 2, 5], o_id=3, decode=dec) is None  # o never named


def test_keys():
    assert cf.template_key("{} is in", 2, [7, 8]) == "{} is in|s2|g7.8"
    assert cf.template_key("{} is in", 2, []) == "{} is in|s2|g"
    assert cf.partner_key("{} is in", 2) == "{} is in|s2"


def test_eligible_partners():
    me = {"case_id": 1, "subject_ids": [5], "o_id": 10, "new_id": 11}
    group = [{"case_id": 1, "subject_ids": [5], "o_id": 12},   # itself
             {"case_id": 2, "subject_ids": [6], "o_id": 10},   # same object
             {"case_id": 3, "subject_ids": [7], "o_id": 11},   # object is my target_new
             {"case_id": 4, "subject_ids": [5], "o_id": 12},   # same subject
             {"case_id": 5, "subject_ids": [8], "o_id": 12}]
    assert [p["case_id"] for p in cf.eligible_partners(me, group)] == [5]


def test_build_counts_and_admission(word_tokenizer):
    records, generate = make_counterfact(word_tokenizer)
    out = cf.build(records, word_tokenizer, generate)
    assert out["counts"] == {
        "records": 38, "multi_token_target": 1, "segment_misaligned": 0, "pool": 37, "not_known": 1,
        "no_partner": 2, "known_with_partner": 34, "templates": 3, "admitted_templates": 1, "admitted": 30,
    }
    assert out["template_floor"] == 30
    admitted = {k for k, v in out["templates"].items() if v["admitted"]}
    assert admitted == {"The capital of {} is|s1|g"}
    assert len(out["survivors"]) == 34
    by_id = {s["case_id"]: s for s in out["survivors"]}
    the = encode(word_tokenizer, " the")[0]
    assert by_id[1]["suffix_ids"] == [the] and by_id[1]["template_key"] == f"The capital of {{}} is|s1|g{the}"
    s = by_id[5]
    whole = encode(word_tokenizer, "The capital of Subj5 is")
    assert s["prefix_ids"] + s["subject_ids"] + s["rest_ids"] == whole and s["suffix_ids"] == []
    assert s["o_id"] == encode(word_tokenizer, " Oslo")[0] and s["new_id"] == encode(word_tokenizer, " Berlin")[0]
    assert 0 not in by_id and 50 not in by_id and 32 not in by_id
    # the pool keeps non-known records as partners (the partner need not pass the filter)
    assert 0 in {p["case_id"] for p in out["partners"]["The capital of {} is|s1"]}


@torch.no_grad()
def test_greedy_shapes_and_first_token(tiny_model):
    prompts = [[5, 6, 7], [8, 9, 10], [11, 12, 13, 14]]
    out = cf.greedy(tiny_model, prompts, max_new=4, batch_size=2)
    assert [len(g) for g in out] == [4, 4, 4] and all(0 <= t < 50 for g in out for t in g)
    assert out == cf.greedy(tiny_model, prompts, max_new=4, batch_size=2)
    first = tiny_model(torch.tensor([prompts[2]]))[0, -1].argmax().item()
    assert cf.greedy(tiny_model, [prompts[2]], max_new=1, batch_size=1) == [[first]]
