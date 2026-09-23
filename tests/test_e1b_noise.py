"""Noise-floor summaries, size rules, the gate guard, and a tiny-model sweep."""

import json
import statistics as stats

import pytest
import torch

from src.lesion import e1b_noise as nz
from src.lesion.runner import run
from src.lesion.spec import MLP, Head, MeanReference


def test_components_and_seeds():
    assert nz.COMPONENTS == tuple([MLP(l) for l in range(12)] + [Head(l, 0) for l in range(12)])
    assert nz.REF_SEEDS == (0, 1, 2, 3, 4)


def test_noise_spec():
    s = nz.noise_spec(MLP(3), ref_n=1000, ref_seed=2)
    assert s.value == "mean" and s.reference == MeanReference("corrupt", 1000, 2, "template")
    assert s.component_type == "node" and s.direction == "ablate-clean" and s.freeze_patterns is False


def test_summarise_takes_the_larger_of_spread_and_sem():
    effects = {0: 1.0, 1: 1.2, 2: 0.8, 3: 1.1, 4: 0.9}
    sd = stats.stdev(effects.values())
    r = nz.summarise("L0.mlp", effects, sem0=0.05)
    assert r["ref_seed_sd"] == pytest.approx(sd) and r["floor"] == pytest.approx(sd) and r["floor_source"] == "ref_seed_sd"
    assert r["effect_mean_by_ref_seed"] == {"0": 1.0, "1": 1.2, "2": 0.8, "3": 1.1, "4": 0.9}
    r = nz.summarise("L0.mlp", effects, sem0=0.3)
    assert r["floor"] == 0.3 and r["floor_source"] == "sem" and r["sem_seed0"] == 0.3


def test_sizes():
    assert nz.sizes(None, None, 1000) == (2000, 1000)
    assert nz.sizes(640, None, 1000) == (640, 640)     # factual: clamp the reference, logged
    assert nz.sizes(2400, None, 1000) == (2400, 1000)
    assert nz.sizes(None, 500, 1000) == (500, 1000)


def test_require_gate_pass(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        nz.require_gate_pass(tmp_path / "none.json")
    p = tmp_path / "g.json"
    p.write_text(json.dumps({"verdict": {"pass": False}}))
    with pytest.raises(ValueError, match="did not pass"):
        nz.require_gate_pass(p)
    p.write_text(json.dumps({"verdict": None, "pre_registered": False}))
    with pytest.raises(ValueError, match="no pre-registered verdict"):
        nz.require_gate_pass(p)
    p.write_text(json.dumps({"verdict": {"pass": True}}))
    nz.require_gate_pass(p)


@torch.no_grad()
def test_measure_floor_on_the_tiny_model(tiny_model, tiny_battery):
    rows = nz.measure_floor(tiny_model, tiny_battery, (MLP(0), Head(1, 0)), (0, 1),
                            n=6, seed=0, ref_n=8, prepend_bos=False, batch_size=4)
    assert [r["component"] for r in rows] == ["L0.mlp", "L1H0"]
    assert set(rows[0]["effect_mean_by_ref_seed"]) == {"0", "1"}
    direct = run(tiny_model, nz.noise_spec(MLP(0), 8, 0), tiny_battery, 6, 0, False, 4)
    assert rows[0]["effect_mean_by_ref_seed"]["0"] == direct.aggregates["effect"]["ld"]["effect_mean"]
    assert rows[0]["sem_seed0"] == direct.aggregates["effect"]["ld"]["sem"]
