"""E2 validation gates on the real model (the E2 spec's hard stops): the set
machinery agrees bitwise with the single-component path on GPT-2, and the
composition scores agree with TransformerLens. GPU, slow."""

import pytest
import torch

from src.lesion.evaluators import composition_scores
from src.lesion.induction import InductionBattery
from src.lesion.ioi import IOIBattery
from src.lesion.knockout import KnockoutSetSpec, Member, compute_set_mean_reference, run_set
from src.lesion.reference import compute_mean_reference
from src.lesion.runner import COLUMNS, run
from src.lesion.spec import AblationSpec, All, Head, Labels, MeanReference

pytestmark = pytest.mark.slow

REF = MeanReference("corrupt", 2000, 0, "template")


@pytest.fixture(scope="module")
def gpt2():
    from src.lesion.model import load_model, set_determinism

    set_determinism(0)
    return load_model("cuda")


@pytest.fixture(scope="module")
def tok():
    from src.lesion.model import plain_tokenizer

    return plain_tokenizer()


def battery(item, tok):
    return (IOIBattery(tok), False) if item == "ioi" else (InductionBattery(tok), True)


@torch.no_grad()
@pytest.mark.parametrize("item,h", [("ioi", Head(9, 6)), ("induction", Head(5, 5))])
def test_set_mean_reference_equals_reference_py(gpt2, tok, item, h):
    b, bos = battery(item, tok)
    single = compute_mean_reference(gpt2, REF, h, b, bos, 128)
    multi = compute_set_mean_reference(gpt2, REF, (h.layer,), b, bos, 128)
    assert single.counts == multi.counts
    for t, v in single.per_template.items():
        assert torch.equal(multi.per_template[t][h.layer][:, h.head, :], v), t


CASES = [("ioi", Head(9, 6), Labels(("END",)), False), ("induction", Head(5, 5), All(), False),
         ("induction", Head(5, 5), All(), True)]


@torch.no_grad()
@pytest.mark.parametrize("value", ["zero", "mean", "resample"])
@pytest.mark.parametrize("item,h,positions,freeze", CASES)
def test_one_member_set_equals_the_node_run(gpt2, tok, value, item, h, positions, freeze):
    b, bos = battery(item, tok)
    ref = REF if value == "mean" else None
    single = AblationSpec(component=h, value=value, reference=ref, component_type="node", receiver=None,
                          mlp_convention=None, positions=positions, direction="ablate-clean", freeze_patterns=freeze)
    ks = KnockoutSetSpec(members=(Member(h, positions),), complement=False, value=value, reference=ref,
                         direction="ablate-clean", freeze_patterns=freeze, granularity="heads")
    a = run(gpt2, single, b, 256, 0, bos, 128)
    s = run_set(gpt2, ks, b, 256, 0, bos, 128)
    for col in COLUMNS:
        assert torch.equal(a.columns[col], s.columns[col]), col


@torch.no_grad()
@pytest.mark.parametrize("item", ["ioi", "induction"])
def test_empty_set_is_the_clean_pass(gpt2, tok, item):
    b, bos = battery(item, tok)
    ks = KnockoutSetSpec(members=(), complement=False, value="zero", reference=None, direction="ablate-clean",
                         freeze_patterns=False, granularity="heads")
    r = run_set(gpt2, ks, b, 256, 0, bos, 128)
    assert torch.equal(r.columns["ld_ablated"], r.columns["ld_clean"])


@torch.no_grad()
def test_composition_matches_transformer_lens(gpt2):
    """Per layer pair: TransformerLens's all-pairs call would build a ~4 GB
    intermediate on GPT-2 small."""
    from transformer_lens import utils

    ours = composition_scores(gpt2.W_Q, gpt2.W_K, gpt2.W_V, gpt2.W_O)
    OV, QK = gpt2.OV, gpt2.QK
    for l1, l2 in ((0, 3), (2, 5), (4, 5), (4, 6), (9, 10)):
        right = {"Q": QK[l2], "K": QK[l2].T, "V": OV[l2]}
        for mode in "QKV":
            tl = utils.composition_scores(OV[l1], right[mode], broadcast_dims=True).double().cpu()  # [H1, H2]
            assert torch.allclose(ours[mode][l1, :, l2, :], tl, rtol=1e-3, atol=1e-6), (mode, l1, l2)
