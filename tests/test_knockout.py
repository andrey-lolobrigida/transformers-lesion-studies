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


from src.lesion.knockout import compute_set_mean_reference, run_set  # noqa: E402
from src.lesion.reference import ReferenceError, compute_mean_reference  # noqa: E402
from src.lesion.runner import COLUMNS, run  # noqa: E402
from src.lesion.spec import AblationSpec  # noqa: E402


@torch.no_grad()
@pytest.mark.parametrize("value", ["zero", "mean", "resample"])
@pytest.mark.parametrize("freeze", [False, True])
@pytest.mark.parametrize("positions", [All(), Labels(("X",))])
@pytest.mark.parametrize("direction", ["ablate-clean", "restore-clean"])
def test_one_member_set_equals_the_node_run(tiny_model, tiny_battery, value, freeze, positions, direction):
    ref = REF if value == "mean" else None
    single = AblationSpec(component=Head(1, 0), value=value, reference=ref, component_type="node", receiver=None,
                          mlp_convention=None, positions=positions, direction=direction, freeze_patterns=freeze)
    a = run(tiny_model, single, tiny_battery, n=8, seed=0, prepend_bos=False, batch_size=4)
    b = run_set(tiny_model, ks([Member(Head(1, 0), positions)], value=value, reference=ref, direction=direction,
                               freeze=freeze), tiny_battery, n=8, seed=0, prepend_bos=False, batch_size=4)
    for col in COLUMNS:
        assert torch.equal(a.columns[col], b.columns[col]), col
    assert a.aggregates == b.aggregates and a.destination == b.destination
    if value == "mean":
        assert a.reference_summary["per_template_counts"] == b.reference_summary["per_template_counts"]


@torch.no_grad()
@pytest.mark.parametrize("value", ["zero", "mean", "resample"])
@pytest.mark.parametrize("freeze", [False, True])
def test_empty_set_is_the_clean_pass(tiny_model, tiny_battery, value, freeze):
    r = run_set(tiny_model, ks(value=value, reference=REF if value == "mean" else None, freeze=freeze),
                tiny_battery, 8, 0, False, 4)
    for name in ("ld", "p_c", "c_over_s"):
        assert torch.equal(r.columns[f"{name}_ablated"], r.columns[f"{name}_clean"])


@torch.no_grad()
def test_empty_complement_knocks_out_every_head(tiny_model, tiny_battery):
    r = run_set(tiny_model, ks(complement=True), tiny_battery, 4, 0, False, 4)
    toks = torch.tensor([p.clean_ids for p in tiny_battery.pairs(4, 0, False)])
    out = tiny_model.run_with_hooks(toks, fwd_hooks=[(f"blocks.{l}.attn.hook_z", lambda x, hook: torch.zeros_like(x))
                                                     for l in range(2)])
    assert torch.equal(r.columns["ld_ablated"], out[:, -1, 1] - out[:, -1, 2])


@torch.no_grad()
def test_two_members_equal_stacked_node_hooks(tiny_model, tiny_battery):
    r = run_set(tiny_model, ks([Member(Head(0, 1), Labels(("X",))), Member(Head(1, 0), All())]),
                tiny_battery, 4, 0, False, 4)
    toks = torch.tensor([p.clean_ids for p in tiny_battery.pairs(4, 0, False)])

    def z01(x, hook):
        x = x.clone()
        x[:, 2, 1, :] = 0
        return x

    def z10(x, hook):
        x = x.clone()
        x[:, :, 0, :] = 0
        return x

    out = tiny_model.run_with_hooks(toks, fwd_hooks=[("blocks.0.attn.hook_z", z01), ("blocks.1.attn.hook_z", z10)])
    assert torch.equal(r.columns["ld_ablated"], out[:, -1, 1] - out[:, -1, 2])


@torch.no_grad()
def test_set_mean_reference_equals_reference_py(tiny_model, tiny_battery):
    s = compute_set_mean_reference(tiny_model, REF, (0, 1), tiny_battery, False, 3)
    for h in (Head(0, 0), Head(0, 1), Head(1, 1)):
        single = compute_mean_reference(tiny_model, REF, h, tiny_battery, False, 3)
        assert s.counts == single.counts
        for t, v in single.per_template.items():
            assert torch.equal(s.per_template[t][h.layer][:, h.head, :], v)
    summ = s.summary()
    assert summ["n"] == 8 and summ["per_template_counts"] == {"A": 4, "B": 4}
    assert summ["hook"] == ["blocks.0.attn.hook_z", "blocks.1.attn.hook_z"]
    assert s.value_for(1, ["A", "B", "A"], 6).shape == (3, 6, 2, 8)
    with pytest.raises(ReferenceError):
        s.value_for(0, ["C"], 6)  # a template with no reference prompt is a hard stop
    with pytest.raises(ReferenceError):
        s.value_for(0, ["A"], 7)


@torch.no_grad()
@pytest.mark.parametrize("spec", [
    ks([Member(Head(1, 1), Labels(("X",)))], complement=True, value="mean", reference=REF),
    ks([Member(Head(0, 0), All()), Member(Head(1, 0), Labels(("END",)))], value="resample", freeze=True),
])
def test_set_batch_invariance(tiny_model, tiny_battery, spec):
    a = run_set(tiny_model, spec, tiny_battery, 8, 0, False, 1)
    b = run_set(tiny_model, spec, tiny_battery, 8, 0, False, 8)
    for col in COLUMNS:
        assert torch.equal(a.columns[col], b.columns[col]), col


@torch.no_grad()
def test_set_bounds_are_hard_stops(tiny_model, tiny_battery):
    for bad in (Member(Head(2, 0), All()), Member(Head(0, 2), All()), Member(Head(0, 0), Labels(("S2",)))):
        with pytest.raises(SpecError):
            run_set(tiny_model, ks([bad]), tiny_battery, 2, 0, False, 2)
