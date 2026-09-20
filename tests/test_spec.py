"""AblationSpec: every conditional field present exactly when required; JSON round trip."""

import pytest

from src.lesion.spec import (
    MLP, AblationSpec, All, Head, Indices, Inputs, Labels, Logits, MeanReference, SpecError,
)

REF = MeanReference(battery_side="corrupt", n=100, seed=0, match="template")


def node(**kw):
    base = dict(component=Head(9, 9), value="zero", reference=None, component_type="node", receiver=None,
                mlp_convention=None, positions=All(), direction="ablate-clean", freeze_patterns=False)
    base.update(kw)
    return AblationSpec(**base)


def edge(**kw):
    base = dict(component=Head(9, 9), value="resample", reference=None, component_type="edge",
                receiver=Logits(), mlp_convention="wang", positions=Labels(("END",)),
                direction="ablate-clean", freeze_patterns=False)
    base.update(kw)
    return AblationSpec(**base)


@pytest.mark.parametrize("spec", [
    node(),
    node(value="mean", reference=REF, positions=Labels(("END", "S2")), freeze_patterns=True),
    node(component=MLP(0), value="resample", direction="restore-clean", positions=Indices((3, 7))),
    edge(),
    edge(mlp_convention="term", receiver=Inputs(((10, 7, "q", "END"), (11, 10, "v", "S2")))),
    edge(component=MLP(3), value="mean", reference=REF),
])
def test_round_trip(spec):
    j = spec.to_json()
    assert AblationSpec.from_json(j) == spec
    import json
    assert AblationSpec.from_json(json.loads(json.dumps(j))) == spec


def test_json_has_a_key_per_axis():
    keys = set(node().to_json())
    assert {"granularity", "component", "component_type", "value", "reference", "receiver",
            "mlp_convention", "positions", "direction", "set", "freeze_patterns"} <= keys
    assert node().to_json()["set"] == "single-component"
    assert node().to_json()["granularity"] == "head"
    assert node(component=MLP(2)).to_json()["granularity"] == "mlp-layer"


def test_refusals():
    with pytest.raises(SpecError):
        edge(freeze_patterns=True)  # freeze + edge
    with pytest.raises(SpecError):
        node(value="mean")  # mean without reference
    with pytest.raises(SpecError):
        node(reference=REF)  # reference without mean
    with pytest.raises(SpecError):
        edge(receiver=None)  # edge without receiver
    with pytest.raises(SpecError):
        edge(mlp_convention=None)  # edge without convention
    with pytest.raises(SpecError):
        node(receiver=Logits())  # receiver on a node spec
    with pytest.raises(SpecError):
        node(mlp_convention="wang")  # convention on a node spec
    with pytest.raises(SpecError):
        edge(receiver=Inputs(((9, 0, "q", "END"),)))  # target layer == sender layer: empty path
    with pytest.raises(SpecError):
        edge(receiver=Inputs(((3, 0, "k", "END"),)))  # target below sender
    with pytest.raises(SpecError):
        edge(receiver=Inputs(()))  # no targets
    with pytest.raises(SpecError):
        node(positions=Labels(()))
    with pytest.raises(SpecError):
        node(positions=Indices((-1,)))
    with pytest.raises(SpecError):
        node(value="drop")
    with pytest.raises(SpecError):
        node(direction="sideways")


def test_direct_effect_definition():
    assert node().direct_effect_definition is None
    assert edge().direct_effect_definition == "wang"
    assert edge(mlp_convention="term").direct_effect_definition == "term"
    assert edge(receiver=Inputs(((10, 0, "q", "END"),))).direct_effect_definition is None


def test_component_label():
    assert node().component_label() == "L9H9"
    assert node(component=MLP(0)).component_label() == "L0.mlp"
