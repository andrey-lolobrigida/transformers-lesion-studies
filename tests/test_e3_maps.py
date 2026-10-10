"""E3 figures from a synthetic tests.json: layout, scale, and the files written."""

import numpy as np

from src.lesion import e3_maps as M
from src.lesion.e3_prereg import COMPONENTS, MAPS, VALUES, label
from src.lesion.spec import Head


def synthetic_tests(item="ioi"):
    """Head effect = layer + head / 100 (largest |head| 11.11); MLP0 = 1000, other MLPs 1.0;
    layer 9 clears Holm; layer-11 deltas are exact zeros."""
    out = []
    for map_id in [m.id for m in MAPS] + [f"delta_{v}" for v in VALUES]:
        for c in COMPONENTS:
            eff = c.layer + c.head / 100 if isinstance(c, Head) else (1000.0 if c.layer == 0 else 1.0)
            exact = map_id.startswith("delta") and c.layer == 11
            out.append({"item": item, "map": map_id, "component": label(c), "effect": 0.0 if exact else eff,
                        "reject": c.layer == 9, "tested": not exact})
    return out


def by_key(tests):
    return {(t["item"], t["map"], t["component"]): t for t in tests}


def test_panel_layout():
    p = M.panel(by_key(synthetic_tests()), "ioi", "total_zero_unfrozen")
    assert p["heads"].shape == (12, 12) and p["mlp"].shape == (12,)
    assert p["heads"][3, 7] == 3.07 and p["mlp"][5] == 1.0 and p["mlp"][0] == 1000.0
    assert p["reject_heads"][9].all() and not p["reject_heads"][8].any() and p["reject_mlp"][9]
    d = M.panel(by_key(synthetic_tests()), "ioi", "delta_mean")
    assert d["exact_heads"][11].all() and d["exact_mlp"][11] and not d["exact_heads"][10].any()


def test_scale_from_heads_and_clipped_mlps():
    p = M.panel(by_key(synthetic_tests()), "ioi", "direct_zero")
    assert np.isclose(M.scale_limit([p], 1.0), 11.11)
    assert np.isclose(M.scale_limit([p], 2.0), 5.555)
    assert M.clipped(p, M.scale_limit([p], 1.0), 1.0) == [0]


def test_render_writes_every_group_in_both_scales(tmp_path):
    paths = M.render(synthetic_tests(), {"ioi": 3.59}, tmp_path, items=("ioi",))
    assert sorted(p.name for p in paths) == sorted(f"ioi_{g}_{s}.png" for g in ("total", "direct", "delta")
                                                   for s in ("raw", "scaled"))
    for p in paths:
        assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_colorbar_label_states_sign_and_scale():
    sign = "red: ld lowered, blue: ld raised"
    assert M.colorbar_label("total", "raw", 3.59) == f"effect on the mean logit difference (logits)\n{sign}"
    assert M.colorbar_label("direct", "raw", 3.59) == M.colorbar_label("total", "raw", 3.59)
    assert M.colorbar_label("delta", "raw", 3.59) == f"frozen effect minus unfrozen effect (logits)\n{sign}"
    assert M.colorbar_label("total", "scaled", 3.59) == (
        f"effect on the mean logit difference\n/ clean-minus-corrupt gap (3.590)\n{sign}")
    assert "gap (3.590)" in M.colorbar_label("delta", "scaled", 3.59)


def test_figures_record_hashes_every_file_and_names_its_inputs(tmp_path):
    import hashlib

    paths = M.render(synthetic_tests(), {"ioi": 3.59}, tmp_path, items=("ioi",))
    env = {"model": {"revision": "m0"}}
    rec = M.figures_record(paths, {"code_rev": "t0", "prompt_seed": 0, "model_revision": "m0"},
                           {"results/E1b/gate/ioi/p_ABC.json": {"environment": env}}, "cmd", "abc")
    assert rec["command"] == "cmd" and rec["code_rev"] == "abc" and rec["model_revision"] == "m0"
    assert rec["prompt_seed"] == 0 and rec["inputs"]["selection/tests.json"] == {"code_rev": "t0"}
    assert rec["files"] == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def test_figures_record_refuses_mixed_model_revisions(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="model revisions"):
        M.figures_record([], {"code_rev": "t0", "prompt_seed": 0, "model_revision": "m0"},
                         {"g.json": {"environment": {"model": {"revision": "m1"}}}}, "cmd", "abc")
