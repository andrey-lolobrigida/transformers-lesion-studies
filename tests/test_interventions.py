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


# --- edge (Task 6) ---

from src.lesion.interventions import run_edge  # noqa: E402
from src.lesion.spec import Inputs, Logits  # noqa: E402


def edge(component=Head(0, 0), value="zero", receiver=Logits(), convention="wang", positions=All()):
    return AblationSpec(component=component, value=value, reference=None, component_type="edge",
                        receiver=receiver, mlp_convention=convention, positions=positions,
                        direction="ablate-clean", freeze_patterns=False)


LABELS7 = [{"END": 6, "MID": 3}]


@torch.no_grad()
def test_edge_identity_both_conventions(tiny_model, toks):
    """Sender set to its own B value == plain forward, under wang and term."""
    base = tiny_model(toks)
    mask = position_mask(All(), LABELS7, 7, "cpu")
    for comp in (Head(0, 1), Head(1, 0), MLP(0), MLP(1)):
        v = sender_cache(tiny_model, toks, comp)
        for conv in ("wang", "term"):
            out = run_edge(tiny_model, edge(comp, "resample", Logits(), conv), toks, mask, v, LABELS7)
            assert torch.equal(out, base), (comp, conv)
    v = sender_cache(tiny_model, toks, Head(0, 1))
    for conv in ("wang", "term"):
        rec = Inputs(((1, 0, "q", "END"), (1, 1, "v", "MID")))
        out = run_edge(tiny_model, edge(Head(0, 1), "resample", rec, conv), toks, mask, v, LABELS7)
        assert torch.equal(out, base), conv


@torch.no_grad()
def test_convention_split(tiny_model, toks):
    """wang != term for a head sender to Logits (the same block's MLP sits between);
    equal when the sender is the last layer's MLP (no MLP follows it)."""
    mask = position_mask(All(), LABELS7, 7, "cpu")
    v = zero_value(Head(1, 0), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    wang = run_edge(tiny_model, edge(Head(1, 0), "zero", Logits(), "wang"), toks, mask, v, LABELS7)
    term = run_edge(tiny_model, edge(Head(1, 0), "zero", Logits(), "term"), toks, mask, v, LABELS7)
    assert not torch.equal(wang, term)
    v = zero_value(MLP(1), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    wang = run_edge(tiny_model, edge(MLP(1), "zero", Logits(), "wang"), toks, mask, v, LABELS7)
    term = run_edge(tiny_model, edge(MLP(1), "zero", Logits(), "term"), toks, mask, v, LABELS7)
    assert torch.equal(wang, term)


@torch.no_grad()
def test_edge_to_logits_differs_from_node(tiny_model, toks):
    """Node zeroing lets layer-1 heads respond; edge-to-logits pins them. The two
    are different measurements and must not coincide on a random model."""
    mask = position_mask(All(), LABELS7, 7, "cpu")
    v = zero_value(Head(0, 0), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    total = run_node(tiny_model, node(Head(0, 0)), toks, mask, v)
    direct = run_edge(tiny_model, edge(Head(0, 0), "zero", Logits(), "wang"), toks, mask, v, LABELS7)
    assert not torch.equal(total, direct)


@torch.no_grad()
def test_edge_to_logits_equals_hand_rolled_pass_c(tiny_model, toks):
    """Pass D with receiver Logits reduces to unembed(ln_final(resid_C))."""
    mask = position_mask(All(), LABELS7, 7, "cpu")
    v = zero_value(Head(0, 0), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    out = run_edge(tiny_model, edge(Head(0, 0), "zero", Logits(), "term"), toks, mask, v, LABELS7)
    _, B = tiny_model.run_with_cache(toks)
    hooks = []
    for layer in range(2):
        def pin(x, hook):
            return B[hook.name]
        hooks.append((f"blocks.{layer}.hook_mlp_out", pin))
        if layer == 0:
            def sender(x, hook):
                return substitute(B[hook.name], mask, v, head=0)
            hooks.append((f"blocks.{layer}.attn.hook_z", sender))
        else:
            hooks.append((f"blocks.{layer}.attn.hook_z", pin))
    grabbed = {}
    def grab(x, hook):
        grabbed["resid"] = x.clone()
        return x
    tiny_model.run_with_hooks(toks, fwd_hooks=hooks + [("blocks.1.hook_resid_post", grab)])
    expected = tiny_model.unembed(tiny_model.ln_final(grabbed["resid"]))
    assert torch.equal(out, expected)


@torch.no_grad()
def test_edge_inputs_receiver_writes_only_the_target(tiny_model, toks):
    """With receiver Inputs, pass D overwrites one head's q at one position;
    logits at earlier positions are bitwise unchanged."""
    mask = position_mask(All(), LABELS7, 7, "cpu")
    v = zero_value(Head(0, 0), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    base = tiny_model(toks)
    out = run_edge(tiny_model, edge(Head(0, 0), "zero", Inputs(((1, 1, "q", "MID"),)), "wang"), toks, mask, v, LABELS7)
    assert torch.equal(out[:, :3], base[:, :3])
    assert not torch.equal(out[:, 3], base[:, 3])
    assert torch.equal(out[:, 4:], base[:, 4:])  # q at MID only affects position MID


@torch.no_grad()
def test_edge_receiver_layer_beyond_model_is_spec_error(tiny_model, toks):
    """AblationSpec only checks the target layer against the sender's layer, not
    against the model; a receiver target beyond the model's layer count must
    still be refused, by run_edge, as a SpecError."""
    mask = position_mask(All(), LABELS7, 7, "cpu")
    v = zero_value(Head(0, 0), 1, 7, tiny_model.cfg, "cpu", torch.float32)
    rec = Inputs(((5, 0, "q", "END"),))
    with pytest.raises(SpecError):
        run_edge(tiny_model, edge(Head(0, 0), "zero", rec, "wang"), toks, mask, v, LABELS7)
