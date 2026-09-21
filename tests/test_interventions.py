# tests/test_interventions.py
"""Node substitution, position masks, pattern freezing. Bitwise via torch.equal."""

import pytest
import torch

from src.lesion.interventions import (
    freeze_hooks, hook_name, node_hooks, position_mask, resolve_label, run_intervened, run_node,
    run_with_pattern_cache, sender_cache, substitute, zero_value,
)
from src.lesion.spec import MLP, AblationSpec, All, Head, Indices, Labels, SpecError


def node(component=Head(0, 0), value="zero", positions=All(), freeze=False):
    return AblationSpec(component=component, value=value, reference=None, component_type="node",
                        receiver=None, mlp_convention=None, positions=positions,
                        direction="ablate-clean", freeze_patterns=freeze)


def test_hook_names():
    assert hook_name(Head(3, 1)) == "blocks.3.attn.hook_z"
    assert hook_name(MLP(11)) == "blocks.11.hook_mlp_out"


def test_position_mask_variants():
    labels = [{"END": 6, "S2": 3}, {"END": 6, "S2": 4}]
    m = position_mask(All(), labels, 7, "cpu")
    assert m.shape == (2, 7) and m.all()
    m = position_mask(Labels(("END", "S2")), labels, 7, "cpu")
    assert m.tolist() == [[False, False, False, True, False, False, True],
                          [False, False, False, False, True, False, True]]
    m = position_mask(Indices((0, 2)), labels, 7, "cpu")
    assert m.tolist() == [[True, False, True, False, False, False, False]] * 2
    with pytest.raises(SpecError):
        position_mask(Labels(("NOPE",)), labels, 7, "cpu")
    with pytest.raises(SpecError):
        position_mask(Indices((7,)), labels, 7, "cpu")
    with pytest.raises(SpecError):
        resolve_label({"END": 1}, "S1")


def test_substitute_writes_only_masked_positions_of_one_head():
    x = torch.arange(2 * 4 * 3 * 2, dtype=torch.float32).reshape(2, 4, 3, 2)
    v = torch.full((2, 4, 2), -1.0)
    mask = torch.zeros(2, 4, dtype=torch.bool)
    mask[0, 1] = True
    mask[1, 3] = True
    y = substitute(x, mask, v, head=1)
    assert not torch.equal(x, y) and torch.equal(x[0, 1, 1], torch.tensor([8.0, 9.0]))  # input untouched
    assert torch.equal(y[0, 1, 1], torch.tensor([-1.0, -1.0])) and torch.equal(y[1, 3, 1], torch.tensor([-1.0, -1.0]))
    y[0, 1, 1] = x[0, 1, 1]
    y[1, 3, 1] = x[1, 3, 1]
    assert torch.equal(x, y)


def test_substitute_mlp_shape():
    x = torch.zeros(1, 3, 5)
    v = torch.ones(1, 3, 5)
    y = substitute(x, torch.tensor([[True, False, True]]), v, head=None)
    assert y.sum().item() == 10.0


@torch.no_grad()
def test_freeze_identity(tiny_model, toks):
    base = tiny_model(toks)
    logits, patterns = run_with_pattern_cache(tiny_model, toks)
    assert torch.equal(logits, base)
    assert set(patterns) == {"blocks.0.attn.hook_pattern", "blocks.1.attn.hook_pattern"}
    frozen = tiny_model.run_with_hooks(toks, fwd_hooks=freeze_hooks(patterns))
    assert torch.equal(frozen, base)


@torch.no_grad()
def test_resample_identity(tiny_model, toks):
    base = tiny_model(toks)
    for comp in (Head(0, 1), Head(1, 0), MLP(0), MLP(1)):
        v = sender_cache(tiny_model, toks, comp)  # x_src == x_dst
        mask = position_mask(All(), [{"END": 6}], 7, "cpu")
        out = run_node(tiny_model, node(comp, "resample"), toks, mask, v)
        assert torch.equal(out, base), comp


@torch.no_grad()
def test_zero_changes_logits(tiny_model, toks):
    base = tiny_model(toks)
    for comp in (Head(0, 1), MLP(1)):
        v = zero_value(comp, 1, 7, tiny_model.cfg, "cpu", base.dtype)
        mask = position_mask(All(), [{"END": 6}], 7, "cpu")
        assert not torch.equal(run_node(tiny_model, node(comp), toks, mask, v), base)


@torch.no_grad()
def test_causality(tiny_model, toks):
    """Zeroing at position 4 leaves logits at positions < 4 bitwise untouched."""
    base = tiny_model(toks)
    for comp in (Head(0, 0), MLP(0)):
        v = zero_value(comp, 1, 7, tiny_model.cfg, "cpu", base.dtype)
        mask = position_mask(Indices((4,)), [{"END": 6}], 7, "cpu")
        out = run_node(tiny_model, node(comp, positions=Indices((4,))), toks, mask, v)
        assert torch.equal(out[:, :4], base[:, :4]), comp
        assert not torch.equal(out[:, 4:], base[:, 4:]), comp


@torch.no_grad()
def test_freeze_composes_with_zero(tiny_model, toks):
    base = tiny_model(toks)
    _, patterns = run_with_pattern_cache(tiny_model, toks)
    v = zero_value(Head(0, 0), 1, 7, tiny_model.cfg, "cpu", base.dtype)
    mask = position_mask(All(), [{"END": 6}], 7, "cpu")
    unfrozen = run_node(tiny_model, node(Head(0, 0)), toks, mask, v)
    frozen = run_node(tiny_model, node(Head(0, 0), freeze=True), toks, mask, v, patterns=patterns)
    # Layer-0 patterns are computed from the residual before head 0 writes, so
    # freezing them changes nothing at layer 0; layer 1 sees a different
    # residual and its patterns move, so the two results differ.
    assert not torch.equal(frozen, unfrozen)
    assert not torch.equal(frozen, base)


@torch.no_grad()
def test_run_intervened_dispatches_node(tiny_model, toks):
    v = zero_value(Head(0, 0), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    mask = position_mask(All(), [{"END": 6}], 7, "cpu")
    a = run_node(tiny_model, node(Head(0, 0)), toks, mask, v)
    b = run_intervened(tiny_model, node(Head(0, 0)), toks, mask, v, [{"END": 6}])
    assert torch.equal(a, b)
