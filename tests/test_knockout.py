"""Set knockout: spec validation, masks, and bitwise agreement with the single-component path."""

import pytest
import torch

from src.lesion.knockout import KnockoutSetSpec, Member, layer_masks
from src.lesion.spec import MLP, All, Head, Indices, Labels, MeanReference, SpecError

REF = MeanReference("corrupt", 8, 1, "template")


def ks(members=(), complement=False, value="zero", reference=None, direction="ablate-clean", freeze=False,
       granularity="heads"):
    return KnockoutSetSpec(members=tuple(members), complement=complement, value=value, reference=reference,
                           direction=direction, freeze_patterns=freeze, granularity=granularity)


def test_validation_refuses_ill_formed_sets():
    with pytest.raises(SpecError):
        ks([Member(Head(0, 0), All()), Member(Head(0, 0), Labels(("X",)))])  # duplicate member
    with pytest.raises(SpecError):
        ks([Member(MLP(0), All())])  # heads only
    with pytest.raises(SpecError):
        ks([Member(Head(0, 0), Labels(()))])
    with pytest.raises(SpecError):
        ks([Member(Head(0, 0), Indices((-1,)))])
    with pytest.raises(SpecError):
        ks([Member(Head(-1, 0), All())])
    with pytest.raises(SpecError):
        ks(value="mean")  # no reference
    with pytest.raises(SpecError):
        ks(value="zero", reference=REF)
    with pytest.raises(SpecError):
        ks(value="mean", reference=MeanReference("corrupt", 8, 0, "pooled"))
    with pytest.raises(SpecError):
        ks(complement=True, direction="restore-clean")
    with pytest.raises(SpecError):
        ks(direction="sideways")
    with pytest.raises(SpecError):
        ks(granularity="mlp")
    ks()  # empty, both modes: the identity and the everything-out validation checks need them
    ks(complement=True)


def test_to_json_records_the_set_block():
    d = ks([Member(Head(1, 0), Labels(("X",)))], value="mean", reference=REF).to_json()
    assert d["granularity"] == "heads" and d["component_type"] == "node" and d["value"] == "mean"
    assert d["reference"] == {"battery_side": "corrupt", "n": 8, "seed": 1, "match": "template"}
    assert d["set"] == {"complement": False,
                        "members": [{"head": {"layer": 1, "head": 0}, "positions": {"kind": "labels", "labels": ["X"]}}]}
    assert ks(complement=True).to_json()["set"] == {"complement": True, "members": []}
    assert ks().direct_effect_definition is None


def test_layers():
    assert ks([Member(Head(1, 0), All()), Member(Head(1, 1), All())]).layers(2) == (1,)
    assert ks(complement=True).layers(3) == (0, 1, 2)


LABELS = [{"X": 2, "END": 5}, {"X": 2, "END": 5}]


def test_layer_masks():
    m = layer_masks(ks([Member(Head(1, 0), Labels(("X",)))]), 2, 2, LABELS, 6, "cpu")
    expect = torch.zeros(2, 6, 2, dtype=torch.bool)
    expect[:, 2, 0] = True
    assert set(m) == {1} and torch.equal(m[1], expect)
    full = layer_masks(ks(complement=True), 2, 2, LABELS, 6, "cpu")
    assert set(full) == {0, 1} and all(v.all() for v in full.values())
    kept = layer_masks(ks([Member(Head(0, 1), Labels(("X",)))], complement=True), 2, 2, LABELS, 6, "cpu")
    exp0 = torch.ones(2, 6, 2, dtype=torch.bool)
    exp0[:, 2, 1] = False
    assert torch.equal(kept[0], exp0) and kept[1].all()
    assert layer_masks(ks(), 2, 2, LABELS, 6, "cpu") == {}
    whole = layer_masks(ks([Member(Head(0, 0), All()), Member(Head(0, 1), All())], complement=True),
                        2, 2, LABELS, 6, "cpu")
    assert set(whole) == {1}  # layer 0 is kept entirely, so it is never written
