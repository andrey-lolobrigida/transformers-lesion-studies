# tests/test_runner.py
"""The runner: direction, batch invariance, aggregate arithmetic, bounds."""

import math

import pytest
import torch

from src.lesion.runner import COLUMNS, aggregate, group_by_length, metrics, run
from src.lesion.spec import MLP, AblationSpec, All, Head, Inputs, Labels, Logits, MeanReference, SpecError
from tests.conftest import TinyBattery


def spec(component=Head(0, 0), value="resample", reference=None, ctype="node", receiver=None, conv=None,
         positions=All(), direction="ablate-clean", freeze=False):
    return AblationSpec(component=component, value=value, reference=reference, component_type=ctype,
                        receiver=receiver, mlp_convention=conv, positions=positions, direction=direction,
                        freeze_patterns=freeze)


def test_group_by_length_matches_e0_order():
    ids = [[1, 2], [1, 2, 3], [4, 5], [6, 7], [8, 9, 10]]
    assert group_by_length(ids, batch_size=2) == [[0, 2], [3], [1, 4]]


def test_metrics_expressions():
    logits = torch.zeros(2, 3, 5)
    logits[0, 2, 1] = 2.0  # answer 1 beats competitor 2 at END=2 for prompt 0
    logits[1, 1, 2] = 1.0  # competitor beats answer at END=1 for prompt 1
    ld, p_c, cs = metrics(logits, torch.tensor([2, 1]), torch.tensor([1, 1]), torch.tensor([2, 2]))
    assert ld.tolist() == [2.0, -1.0] and cs.tolist() == [1.0, 0.0]
    assert torch.equal(p_c, logits[[0, 1], [2, 1]].log_softmax(-1).exp()[:, 1].cpu())


def test_aggregate_arithmetic():
    cols = {
        "ld_clean": torch.tensor([2.0, 4.0, 0.05, 2.0]), "ld_ablated": torch.tensor([1.0, 2.0, 0.05, 1.0]),
        "p_c_clean": torch.tensor([0.5, 0.5, 0.5, 0.5]), "p_c_ablated": torch.tensor([0.25, 0.25, 0.25, 0.25]),
        "c_over_s_clean": torch.tensor([1.0, 1.0, 1.0, 1.0]), "c_over_s_ablated": torch.tensor([1.0, 1.0, 0.0, 1.0]),
    }
    agg = aggregate(cols, ["A", "B", "A", "B"])
    assert agg["clean"]["n"] == 4
    assert agg["clean"]["mean_ld"] == pytest.approx(2.0125)
    assert agg["effect"]["ld"]["effect_mean"] == pytest.approx(1.0)  # positive: the ablation hurt
    assert agg["effect"]["ld"]["sem"] == pytest.approx(torch.tensor([1.0, 2.0, 0.0, 1.0]).std().item() / 2)
    assert agg["effect"]["ld"]["ratio_of_means"] == pytest.approx(1.0125 / 2.0125)
    assert agg["effect"]["ld"]["mean_of_ratios"] == pytest.approx((0.5 + 0.5 + 1.0 + 0.5) / 4)
    assert agg["effect"]["ld"]["n_abs_clean_below_0.1"] == 1
    assert len(agg["effect"]["ld"]["ratio_iqr"]) == 2
    assert agg["effect"]["p_c"]["effect_mean"] == pytest.approx(0.25) and "ratio_of_means" not in agg["effect"]["p_c"]
    assert agg["effect"]["c_over_s"]["effect_mean"] == pytest.approx(0.25)
    assert agg["by_template"]["A"]["n"] == 2 and agg["by_template"]["A"]["clean"]["mean_ld"] == pytest.approx(1.025)
    assert agg["by_template"]["B"]["ablated"]["mean_ld"] == pytest.approx(1.5)


@torch.no_grad()
def test_direction_swap(tiny_model, tiny_battery):
    """restore-clean reads the corrupt prompt's logits and writes clean values."""
    res = run(tiny_model, spec(direction="restore-clean"), tiny_battery, n=4, seed=0, prepend_bos=False, batch_size=4)
    assert res.destination == "corrupt"
    pairs = tiny_battery.pairs(4, 0, False)
    corrupt = torch.tensor([p.corrupt_ids for p in pairs])
    clean = torch.tensor([p.clean_ids for p in pairs])
    base = tiny_model(corrupt)
    assert torch.equal(res.columns["ld_clean"], (base[:, -1, 1] - base[:, -1, 2]))
    _, cache = tiny_model.run_with_cache(clean, names_filter=lambda n: n == "blocks.0.attn.hook_z")

    def write_clean(x, hook):
        x = x.clone()
        x[:, :, 0, :] = cache[hook.name][:, :, 0, :]
        return x

    patched = tiny_model.run_with_hooks(corrupt, fwd_hooks=[("blocks.0.attn.hook_z", write_clean)])
    assert torch.equal(res.columns["ld_ablated"], (patched[:, -1, 1] - patched[:, -1, 2]))
    fwd = run(tiny_model, spec(direction="ablate-clean"), tiny_battery, n=4, seed=0, prepend_bos=False, batch_size=4)
    assert fwd.destination == "clean"
    base_clean = tiny_model(clean)
    assert torch.equal(fwd.columns["ld_clean"], (base_clean[:, -1, 1] - base_clean[:, -1, 2]))


@torch.no_grad()
@pytest.mark.parametrize("s", [
    spec(),
    spec(value="zero", positions=Labels(("X",))),
    spec(value="mean", reference=MeanReference("corrupt", 8, 1, "template")),
    spec(value="mean", reference=MeanReference("clean", 8, 1, "pooled"), component=MLP(0), freeze=True),
    spec(ctype="edge", receiver=Logits(), conv="wang"),
    spec(ctype="edge", receiver=Inputs(((1, 1, "q", "END"),)), conv="term", value="zero"),
])
def test_batch_invariance(tiny_model, tiny_battery, s):
    a = run(tiny_model, s, tiny_battery, n=8, seed=0, prepend_bos=False, batch_size=1)
    b = run(tiny_model, s, tiny_battery, n=8, seed=0, prepend_bos=False, batch_size=8)
    for col in COLUMNS:
        assert torch.equal(a.columns[col], b.columns[col]), col
    assert a.aggregates == b.aggregates
    assert a.batch_size == 1 and b.batch_size == 8


@torch.no_grad()
def test_result_shape(tiny_model, tiny_battery):
    res = run(tiny_model, spec(value="mean", reference=MeanReference("corrupt", 8, 1, "template")),
              tiny_battery, n=6, seed=2, prepend_bos=True, batch_size=4)
    assert set(res.columns) == set(COLUMNS) and all(c.shape == (6,) for c in res.columns.values())
    assert res.templates == ["A", "B", "A", "B", "A", "B"] and res.meta["i"] == [str(i) for i in range(6)]
    assert res.reference_summary["n"] == 8 and res.reference_summary["per_template_counts"] == {"A": 4, "B": 4}
    assert res.prepend_bos is True and res.seconds > 0
    assert set(res.aggregates) == {"clean", "ablated", "effect", "by_template"}


@torch.no_grad()
def test_bounds_are_hard_stops(tiny_model, tiny_battery):
    with pytest.raises(SpecError):
        run(tiny_model, spec(component=Head(2, 0)), tiny_battery, 2, 0, False, 2)
    with pytest.raises(SpecError):
        run(tiny_model, spec(component=Head(0, 2)), tiny_battery, 2, 0, False, 2)
    with pytest.raises(SpecError):
        run(tiny_model, spec(value="zero", positions=Labels(("S2",))), tiny_battery, 2, 0, False, 2)
