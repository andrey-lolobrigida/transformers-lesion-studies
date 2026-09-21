"""CLI parsing and refusals. Nothing here loads a model: load_model is patched to explode."""

import pytest

from src.lesion import ablate
from src.lesion.spec import MLP, All, Head, Indices, Inputs, Labels, Logits, MeanReference

BASE = ["--battery", "ioi", "--component", "L0H0", "--type", "node", "--positions", "all",
        "--direction", "ablate-clean", "--no-freeze"]
MEAN = ["--ref-side", "corrupt", "--ref-n", "100", "--ref-seed", "0", "--ref-match", "template"]


@pytest.fixture(autouse=True)
def never_load_model(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("model loaded before validation finished")

    monkeypatch.setattr("src.lesion.model.load_model", boom)
    monkeypatch.setattr("src.lesion.model.plain_tokenizer", boom)


def parse(argv):
    return ablate.build_parser().parse_args(argv)


def test_parse_component():
    assert ablate.parse_component("L9H9") == Head(9, 9)
    assert ablate.parse_component("L0.mlp") == MLP(0)
    for bad in ("L9", "H9", "L0.attn", "9H9", "L0H", "mlp"):
        with pytest.raises(ValueError):
            ablate.parse_component(bad)


def test_parse_positions():
    assert ablate.parse_positions("all") == All()
    assert ablate.parse_positions("END,S2") == Labels(("END", "S2"))
    assert ablate.parse_positions("idx:3,7") == Indices((3, 7))
    with pytest.raises(ValueError):
        ablate.parse_positions("idx:")


def test_parse_target():
    assert ablate.parse_target("L9H9.q@END") == (9, 9, "q", "END")
    with pytest.raises(ValueError):
        ablate.parse_target("L9H9@END")


def test_specs_from_args_single_value():
    specs = ablate.specs_from_args(parse(BASE + ["--value", "zero"]))
    assert len(specs) == 1 and specs[0].value == "zero" and specs[0].freeze_patterns is False


def test_specs_from_args_all_values_in_order():
    specs = ablate.specs_from_args(parse(BASE + ["--value", "all", *MEAN]))
    assert [s.value for s in specs] == ["zero", "mean", "resample"]
    assert specs[1].reference == MeanReference("corrupt", 100, 0, "template")
    assert specs[0].reference is None and specs[2].reference is None


def test_specs_from_args_edge():
    argv = ["--battery", "ioi", "--component", "L9H9", "--value", "resample", "--type", "edge", "--receiver", "inputs",
            "--target", "L10H7.q@END", "--target", "L11H10.v@S2", "--mlp-convention", "term",
            "--positions", "END", "--direction", "restore-clean", "--no-freeze"]
    (s,) = ablate.specs_from_args(parse(argv))
    assert s.receiver == Inputs(((10, 7, "q", "END"), (11, 10, "v", "S2"))) and s.mlp_convention == "term"
    (s,) = ablate.specs_from_args(parse(argv[:9] + ["logits"] + argv[14:]))  # receiver logits, no targets
    assert s.receiver == Logits()


@pytest.mark.parametrize("argv", [
    BASE[:-1] + ["--value", "zero"],                                            # freeze flag missing
    BASE + ["--value", "mean"],                                                 # mean without reference
    BASE + ["--value", "mean", "--ref-side", "corrupt", "--ref-seed", "0", "--ref-match", "template"],  # no --ref-n
    BASE + ["--value", "all"],                                                  # all includes mean
    ["--battery", "ioi", "--component", "L0H0", "--value", "zero", "--type", "edge", "--receiver", "logits",
     "--mlp-convention", "wang", "--positions", "all", "--direction", "ablate-clean", "--freeze"],   # freeze + edge
    ["--battery", "ioi", "--component", "L0H0", "--value", "zero", "--type", "edge", "--mlp-convention", "wang",
     "--positions", "all", "--direction", "ablate-clean", "--no-freeze"],       # edge without receiver
    ["--battery", "ioi", "--component", "L0H0", "--value", "zero", "--type", "edge", "--receiver", "logits",
     "--positions", "all", "--direction", "ablate-clean", "--no-freeze"],       # edge without convention
    ["--battery", "ioi", "--component", "L5H0", "--value", "zero", "--type", "edge", "--receiver", "inputs",
     "--target", "L5H1.q@END", "--mlp-convention", "wang", "--positions", "all", "--direction", "ablate-clean",
     "--no-freeze"],                                                            # target at sender's layer
    BASE[:6] + ["--positions", "END,NOPE", "--direction", "ablate-clean", "--no-freeze", "--value", "zero"],  # unknown label
    BASE[:6] + ["--positions", "all", "--direction", "ablate-clean", "--no-freeze", "--value", "zero",
                "--type", "edge", "--receiver", "inputs", "--target", "L9H9.q@NOPE", "--mlp-convention", "wang"],
    BASE + ["--value", "zero", "--component", "L0.attn"],                       # bad component
    BASE + ["--value", "zero", "--prepend-bos", "maybe"],                       # bad bool
])
def test_refusals_exit_2_before_model_loads(argv):
    with pytest.raises(SystemExit) as e:
        ablate.main(argv)
    assert e.value.code == 2


def test_defaults_are_visible_in_parsed_args():
    a = parse(BASE + ["--value", "zero"])
    assert (a.n, a.seed, a.prepend_bos, a.batch_size, a.out_dir, a.device) == (1000, 0, "false", 256, "results/E1a", "cuda")
