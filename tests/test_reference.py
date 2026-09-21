# tests/test_reference.py
"""Mean references: matched and pooled; sizes and counts carried; identity on identical prompts."""

import pytest
import torch

from src.lesion.reference import ReferenceError, compute_mean_reference
from src.lesion.spec import MLP, Head, MeanReference
from src.lesion.interventions import sender_cache
from tests.conftest import TinyBattery


@torch.no_grad()
def test_mean_over_identical_prompts_is_the_single_activation(tiny_model):
    """Two identical prompts per template: (x + x) / 2 == x bitwise."""
    battery = TinyBattery(identical=True)
    ref = MeanReference(battery_side="clean", n=4, seed=0, match="template")
    for comp in (Head(1, 0), MLP(0)):
        values = compute_mean_reference(tiny_model, ref, comp, battery, prepend_bos=False, batch_size=4)
        pair = battery.pairs(1, 0, False)[0]
        single = sender_cache(tiny_model, torch.tensor([pair.clean_ids]), comp)[0]
        assert values.counts == {"A": 2, "B": 2} and values.n_prompts == 4
        assert torch.equal(values.per_template["A"], single)
        assert torch.equal(values.per_template["B"], single)
        v = values.value_for(["A", "B", "A"], seq_len=6)
        assert v.shape == (3, 6, single.shape[-1]) and torch.equal(v[2], single)


@torch.no_grad()
def test_matched_and_pooled_differ(tiny_model, tiny_battery):
    matched = compute_mean_reference(
        tiny_model, MeanReference("clean", 8, 0, "template"), Head(0, 1), tiny_battery, False, 8)
    pooled = compute_mean_reference(
        tiny_model, MeanReference("clean", 8, 0, "pooled"), Head(0, 1), tiny_battery, False, 8)
    assert not torch.equal(matched.per_template["A"], matched.per_template["B"])
    assert pooled.per_template is None and pooled.pooled.shape == (tiny_model.cfg.d_head,)
    v = pooled.value_for(["A", "B"], seq_len=6)
    assert v.shape == (2, 6, tiny_model.cfg.d_head)
    assert torch.equal(v[0, 0], pooled.pooled) and torch.equal(v[1, 5], pooled.pooled)
    assert not torch.equal(matched.value_for(["A"], 6), pooled.value_for(["A"], 6))


@torch.no_grad()
def test_battery_side_matters(tiny_model, tiny_battery):
    clean = compute_mean_reference(tiny_model, MeanReference("clean", 8, 0, "pooled"), MLP(1), tiny_battery, False, 8)
    corrupt = compute_mean_reference(tiny_model, MeanReference("corrupt", 8, 0, "pooled"), MLP(1), tiny_battery, False, 8)
    assert not torch.equal(clean.pooled, corrupt.pooled)


@torch.no_grad()
def test_missing_template_is_a_hard_stop(tiny_model, tiny_battery):
    values = compute_mean_reference(tiny_model, MeanReference("clean", 8, 0, "template"), MLP(1), tiny_battery, False, 8)
    with pytest.raises(ReferenceError):
        values.value_for(["C"], seq_len=6)
    with pytest.raises(ReferenceError):
        values.value_for(["A"], seq_len=7)  # length mismatch


@torch.no_grad()
def test_summary_carries_size_seed_match_side(tiny_model, tiny_battery):
    s = compute_mean_reference(tiny_model, MeanReference("corrupt", 8, 3, "template"), MLP(1), tiny_battery, False, 8).summary()
    assert s["n"] == 8 and s["seed"] == 3 and s["match"] == "template" and s["battery_side"] == "corrupt"
    assert s["n_prompts_used"] == 8 and s["per_template_counts"] == {"A": 4, "B": 4}
    assert s["hook"] == "blocks.1.hook_mlp_out"
