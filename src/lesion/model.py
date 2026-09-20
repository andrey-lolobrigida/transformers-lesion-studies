"""GPT-2 small at a pinned HuggingFace revision, and the determinism settings
every run in this project uses. Moved out of ``e0_smoke.py`` in E1a; the E0
artifact and rerun command are unchanged."""

from __future__ import annotations

import os

# Must be set before CUDA initialises for torch.use_deterministic_algorithms.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch  # noqa: E402

MODEL_NAME = "gpt2"
# HuggingFace hub commit for openai-community/gpt2, resolved on 2026-09-20 and
# pinned. Change deliberately, never implicitly.
MODEL_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"


def determinism_flags() -> dict:
    """The flags that get recorded next to every number."""
    return {
        "use_deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
    }


def set_determinism(seed: int) -> dict:
    """Exactly what E0 set, nothing more: the E0 identity check depends on it."""
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    return determinism_flags()


def plain_tokenizer():
    """A tokenizer that adds special tokens only when asked. TransformerLens
    mutates the tokenizer it is given so that BOS is always prepended
    (docs/06-environment.md, gotcha log); this one is kept separate."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)


def load_model(device: str):
    from transformer_lens import HookedTransformer
    from transformers import GPT2LMHeadModel

    hf_model = GPT2LMHeadModel.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)
    model = HookedTransformer.from_pretrained(
        MODEL_NAME, hf_model=hf_model, tokenizer=plain_tokenizer(), device=device
    )
    model.eval()
    return model
