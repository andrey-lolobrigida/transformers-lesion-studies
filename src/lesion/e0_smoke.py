"""E0 smoke test: environment check + one published number.

Steps, in order (each is a hard failure if it does not pass):

1. CUDA is usable and the installed torch build has kernels for this GPU
   (a real matmul on the device, compared against CPU).
2. GPT-2 small loads into TransformerLens at a pinned HuggingFace revision.
3. A hook fires on an activation and can modify it (a hook that multiplies
   ``blocks.0.attn.hook_z`` by 1 leaves the logits bitwise unchanged; a hook
   that zeroes it changes them).
4. Forward passes are bitwise deterministic across two runs of the same batch.
5. The clean mean logit difference on p_IOI is computed and compared with the
   published value: 3.56 over 100,000 samples [wang-2022 §2].

The published number was measured by the paper's released code, which feeds
tokens to the model *without* a BOS token (``prepend_bos=False`` default; a
code comment says GPT-2 small "wasn't trained this way"). TransformerLens
prepends BOS by default. Both are computed and reported side by side; the
no-BOS number is the one that corresponds to the paper's procedure.

Writes ``results/E0/e0_smoke_<seed>.json`` with every number, the seed, the
model revision hash, package versions, and the exact rerun command.

Rerun:
    uv run python -m src.lesion.e0_smoke --n 100000 --seed 0
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from src.lesion.model import (  # noqa: E402  (sets CUBLAS_WORKSPACE_CONFIG before torch)
    MODEL_NAME,
    MODEL_REVISION,
    determinism_flags,
    load_model,
    plain_tokenizer,
    set_determinism,
)

import torch  # noqa: E402

from src.lesion.ioi import IOIPrompt, generate_prompts  # noqa: E402

PUBLISHED_MEAN_LOGIT_DIFF = 3.56  # [wang-2022 §2], 100,000 samples
PUBLISHED_IO_OVER_S = 0.993  # [wang-2022 §2]
PUBLISHED_IO_PROB = 0.49  # [wang-2022 §2]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def step_cuda() -> dict:
    if not torch.cuda.is_available():
        fail("torch.cuda.is_available() is False")
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    arch_list = torch.cuda.get_arch_list()
    a = torch.randn(512, 512, generator=torch.Generator().manual_seed(0))
    b = torch.randn(512, 512, generator=torch.Generator().manual_seed(1))
    try:
        gpu = (a.cuda() @ b.cuda()).cpu()
    except RuntimeError as e:  # no kernel image is the classic sm_120 failure
        fail(f"CUDA matmul failed on {name} (capability {cap}): {e}")
    cpu = a @ b
    max_err = (gpu - cpu).abs().max().item()
    if max_err > 1e-2:
        fail(f"CUDA matmul disagrees with CPU, max abs err {max_err}")
    print(f"[1/5] CUDA ok: {name}, capability {cap}, arch list {arch_list}, matmul max err {max_err:.2e}")
    return {"gpu": name, "capability": list(cap), "torch_arch_list": arch_list, "matmul_max_abs_err": max_err}


def step_load_model(device: str):
    model = load_model(device)
    print(f"[2/5] loaded {MODEL_NAME}@{MODEL_REVISION[:8]} into TransformerLens on {device}: "
          f"{model.cfg.n_layers} layers x {model.cfg.n_heads} heads, d_model {model.cfg.d_model}")
    return model


@torch.no_grad()
def step_hook(model) -> dict:
    toks = model.to_tokens("When Mary and John went to the store, John gave a drink to")
    base = model(toks)
    fired = {"n": 0, "shape": None}

    def identity_hook(z, hook):
        fired["n"] += 1
        fired["shape"] = tuple(z.shape)
        return z * 1.0

    def zero_hook(z, hook):
        return torch.zeros_like(z)

    same = model.run_with_hooks(toks, fwd_hooks=[("blocks.0.attn.hook_z", identity_hook)])
    if fired["n"] != 1:
        fail(f"hook fired {fired['n']} times, expected 1")
    if not torch.equal(same, base):
        fail("identity hook changed the logits")
    zeroed = model.run_with_hooks(toks, fwd_hooks=[("blocks.0.attn.hook_z", zero_hook)])
    if torch.equal(zeroed, base):
        fail("zeroing blocks.0.attn.hook_z did not change the logits")
    print(f"[3/5] hooks ok: blocks.0.attn.hook_z shape {fired['shape']}, identity hook bitwise-neutral, zero hook not")
    return {"hook_point": "blocks.0.attn.hook_z", "z_shape": list(fired["shape"])}


def encode(model, prompts: list[IOIPrompt], prepend_bos: bool) -> list[tuple[list[int], int, int]]:
    """Return (token ids, IO id, S id) per prompt.

    TransformerLens mutates the tokenizer it is given so that it prepends BOS
    on every call; a fresh plain tokenizer is used here with special tokens
    off so that BOS is added only when asked. Names being single tokens with a
    leading space is checked rather than assumed."""
    tok = plain_tokenizer()
    bos = model.tokenizer.bos_token_id
    out = []
    for p in prompts:
        ids = tok(p.prompt, add_special_tokens=False).input_ids
        if ids[0] == bos:
            fail("plain tokenizer prepended BOS unexpectedly")
        io = tok(" " + p.io, add_special_tokens=False).input_ids
        s = tok(" " + p.s, add_special_tokens=False).input_ids
        if len(io) != 1 or len(s) != 1:
            fail(f"name is not a single token: {p.io!r} -> {io}, {p.s!r} -> {s}")
        # Alignment guarantee the paper relies on: prompt tokens + answer token
        # is exactly the tokenisation of the full sentence.
        if ids + io != tok(p.text, add_special_tokens=False).input_ids:
            fail(f"tokenisation of prompt + answer differs from the full sentence: {p.text!r}")
        if prepend_bos:
            ids = [bos] + ids
        out.append((ids, io[0], s[0]))
    return out


@torch.no_grad()
def final_logits_by_length(model, encoded, batch_size: int, device: str):
    """Run prompts grouped by token length so no padding or attention mask is
    involved. Yields (indices, final-position logits) per batch."""
    groups: dict[int, list[int]] = defaultdict(list)
    for i, (ids, _, _) in enumerate(encoded):
        groups[len(ids)].append(i)
    for length in sorted(groups):
        idxs = groups[length]
        for start in range(0, len(idxs), batch_size):
            chunk = idxs[start : start + batch_size]
            toks = torch.tensor([encoded[i][0] for i in chunk], device=device)
            logits = model(toks)[:, -1, :].float()
            yield chunk, logits


@torch.no_grad()
def step_determinism(model, encoded, device: str) -> dict:
    chunk, first = max(final_logits_by_length(model, encoded, 256, device), key=lambda cl: len(cl[0]))
    _, second = max(final_logits_by_length(model, encoded, 256, device), key=lambda cl: len(cl[0]))
    if not torch.equal(first, second):
        fail(f"forward pass not bitwise deterministic; max diff {(first - second).abs().max().item()}")
    print(f"[4/5] determinism ok: two passes over {len(chunk)} prompts bitwise identical")
    return {"bitwise_identical": True, "n_checked": len(chunk), **determinism_flags()}


@torch.no_grad()
def step_ioi(model, prompts, prepend_bos: bool, batch_size: int, device: str) -> dict:
    encoded = encode(model, prompts, prepend_bos)
    n = len(encoded)
    logit_diff = torch.empty(n)
    io_prob = torch.empty(n)
    t0 = time.time()
    for chunk, logits in final_logits_by_length(model, encoded, batch_size, device):
        io_ids = torch.tensor([encoded[i][1] for i in chunk], device=logits.device)
        s_ids = torch.tensor([encoded[i][2] for i in chunk], device=logits.device)
        io_logit = logits.gather(1, io_ids[:, None])[:, 0]
        s_logit = logits.gather(1, s_ids[:, None])[:, 0]
        probs = logits.log_softmax(-1).exp()
        idx = torch.tensor(chunk)
        logit_diff[idx] = (io_logit - s_logit).cpu()
        io_prob[idx] = probs.gather(1, io_ids[:, None])[:, 0].cpu()
    elapsed = time.time() - t0
    res = {
        "prepend_bos": prepend_bos,
        "n": n,
        "mean_logit_diff": logit_diff.mean().item(),
        "std_logit_diff": logit_diff.std().item(),
        "sem_logit_diff": (logit_diff.std() / n**0.5).item(),
        "io_over_s_fraction": (logit_diff > 0).float().mean().item(),
        "mean_io_prob": io_prob.mean().item(),
        "by_order": {},
        "seconds": elapsed,
    }
    for order in ("BABA", "ABBA"):
        mask = torch.tensor([p.order == order for p in prompts])
        res["by_order"][order] = {"n": int(mask.sum()), "mean_logit_diff": logit_diff[mask].mean().item()}
    # Per-(order, template) means: the template mix is the one design choice
    # the paper text leaves open (its code's "mixed" mode with the default
    # template count uses the first 7 templates of each order, 14 in all).
    res["by_template"] = {}
    for order in ("BABA", "ABBA"):
        for t in range(15):
            mask = torch.tensor([p.order == order and p.template_idx == t for p in prompts])
            res["by_template"][f"{order}/{t}"] = {"n": int(mask.sum()), "mean_logit_diff": logit_diff[mask].mean().item()}
    first7 = [v["mean_logit_diff"] for k, v in res["by_template"].items() if int(k.split("/")[1]) < 7]
    res["derived_mean_first_7_templates_each_order"] = sum(first7) / len(first7)
    print(f"      prepend_bos={prepend_bos!s:5}  n={n}  mean logit diff {res['mean_logit_diff']:.4f} "
          f"(sem {res['sem_logit_diff']:.4f})  IO>S {res['io_over_s_fraction']:.4f}  "
          f"IO prob {res['mean_io_prob']:.4f}  [{elapsed:.1f}s]")
    print(f"        per-template means: min {min(v['mean_logit_diff'] for v in res['by_template'].values()):.3f}, "
          f"max {max(v['mean_logit_diff'] for v in res['by_template'].values()):.3f}; "
          f"first-7-templates-per-order variant {res['derived_mean_first_7_templates_each_order']:.4f}")
    return res


def git_rev() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=100_000, help="number of p_IOI samples (paper: 100,000)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", default="results/E0")
    args = ap.parse_args()

    set_determinism(args.seed)

    from importlib.metadata import version as pkg_version

    record: dict = {
        "phase": "E0",
        "command": "uv run python -m src.lesion.e0_smoke " + " ".join(sys.argv[1:]),
        "seed": args.seed,
        "repo_commit": git_rev(),
        "model": {"name": MODEL_NAME, "revision": MODEL_REVISION},
        "versions": {"python": platform.python_version(), "torch": torch.__version__,
                     "cuda": torch.version.cuda, "transformer_lens": pkg_version("transformer-lens"),
                     "transformers": pkg_version("transformers")},
        "published": {"mean_logit_diff": PUBLISHED_MEAN_LOGIT_DIFF, "io_over_s": PUBLISHED_IO_OVER_S,
                      "io_prob": PUBLISHED_IO_PROB, "n": 100_000, "source": "wang-2022 §2"},
    }
    record["cuda"] = step_cuda()
    model = step_load_model(args.device)
    record["hook"] = step_hook(model)
    prompts = generate_prompts(args.n, args.seed)
    record["determinism"] = step_determinism(model, encode(model, prompts[:256], prepend_bos=False), args.device)
    print(f"[5/5] p_IOI clean baseline, {args.n} prompts, seed {args.seed}")
    record["ioi"] = {
        "no_bos": step_ioi(model, prompts, False, args.batch_size, args.device),
        "bos": step_ioi(model, prompts, True, args.batch_size, args.device),
    }
    got = record["ioi"]["no_bos"]["mean_logit_diff"]
    record["reproduces_published"] = {
        "no_bos_mean_logit_diff_rounded_2dp": round(got, 2),
        "matches_3_56_at_2dp": round(got, 2) == PUBLISHED_MEAN_LOGIT_DIFF,
    }
    print(f"      published (no BOS, paper's procedure): {PUBLISHED_MEAN_LOGIT_DIFF}   got: {got:.4f}   "
          f"match at 2 dp: {record['reproduces_published']['matches_3_56_at_2dp']}")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"e0_smoke_seed{args.seed}_n{args.n}.json"
    path.write_text(json.dumps(record, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
