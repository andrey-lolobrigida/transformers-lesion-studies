"""Artifact schema, naming and writer. Per-prompt values go to parquet, the
summary to JSON, both under results/E1a/ (spec, decision 5). The stem encodes
every field of the spec so two different specs cannot share a file and a rerun
overwrites only its own."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import torch

from src.lesion.model import MODEL_NAME, MODEL_REVISION, determinism_flags
from src.lesion.runner import COLUMNS, RunResult
from src.lesion.spec import AblationSpec, All, Head, Labels, Logits


def stem(spec: AblationSpec, battery_name: str, n: int, seed: int, prepend_bos: bool) -> str:
    c = spec.component
    comp = f"L{c.layer}H{c.head}" if isinstance(c, Head) else f"L{c.layer}mlp"
    if spec.value == "mean":
        r = spec.reference
        value = f"mean-{r.battery_side}-n{r.n}-s{r.seed}-{r.match}"
    else:
        value = spec.value
    if spec.component_type == "node":
        ctype = "node"
    elif isinstance(spec.receiver, Logits):
        ctype = f"edge-logits-{spec.mlp_convention}"
    else:
        targets = "+".join(f"L{l}H{h}{i}-{lab}" for l, h, i, lab in spec.receiver.targets)
        ctype = f"edge-inputs-{targets}-{spec.mlp_convention}"
    p = spec.positions
    if isinstance(p, All):
        positions = "all"
    elif isinstance(p, Labels):
        positions = "pos-" + "-".join(p.labels)
    else:
        positions = "idx-" + "-".join(str(i) for i in p.indices)
    parts = [battery_name, comp, value, ctype, positions, spec.direction]
    if spec.freeze_patterns:
        parts.append("frozen")
    parts += [f"n{n}", f"seed{seed}"]
    if prepend_bos:
        parts.append("bos")
    return "_".join(parts)


def git_rev() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def environment_record(model, batch_size: int, seconds: float) -> dict:
    from importlib.metadata import version as pkg_version

    device = str(model.cfg.device)
    gpu = torch.cuda.get_device_name(0) if device.startswith("cuda") and torch.cuda.is_available() else device
    return {
        "repo_commit": git_rev(),
        "model": {"name": MODEL_NAME, "revision": MODEL_REVISION},
        "versions": {"python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda,
                     "transformer_lens": pkg_version("transformer-lens"), "transformers": pkg_version("transformers"),
                     "pyarrow": pa.__version__},
        "gpu": gpu,
        "determinism": determinism_flags(),
        "batch_size": batch_size,
        "seconds": seconds,
    }


def direct_effect_definition(spec: AblationSpec) -> str | None:
    """Written next to every edge-to-logits number so no README can cite the
    project's direct effect without its MLP convention (O-011)."""
    return spec.direct_effect_definition


def effect_sign(spec: AblationSpec) -> str:
    """The direction-dependent reading of ``effect_mean`` (I-1): under
    ablate-clean the columns are the clean prompt, unintervened vs. intervened;
    under restore-clean they are the corrupt prompt, unintervened vs. intervened,
    so the same "positive = the ablation hurt" arithmetic reads oppositely."""
    if spec.direction == "restore-clean":
        return ("positive = restoring the clean value hurt; negative = restoration helped "
                "(unintervened minus intervened, on the corrupt prompt)")
    return "positive = ablating the component hurt (clean minus intervened, on the clean prompt)"


def build_record(result: RunResult, spec: AblationSpec, battery, command: str, environment: dict, cli_args: dict) -> dict:
    return {
        "phase": "E1a",
        "command": command,
        "cli": cli_args,
        "spec": spec.to_json(),
        "environment": environment,
        "battery": {
            "name": battery.name, "n": result.n, "seed": result.seed, "prepend_bos": result.prepend_bos,
            "template_set": battery.template_set, "labels": list(battery.labels),
            "corruption": asdict(battery.corruption),
        },
        "destination_prompt": result.destination,
        "effect_sign": effect_sign(spec),
        "reference": result.reference_summary,
        "results": result.aggregates,
        "direct_effect_definition": direct_effect_definition(spec),
    }


def write(record: dict, result: RunResult, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = stem(result.spec, record["battery"]["name"], result.n, result.seed, result.prepend_bos)
    json_path = out_dir / f"{base}.json"
    parquet_path = out_dir / f"{base}.parquet"
    json_path.write_text(json.dumps(record, indent=2))
    columns = {"idx": list(range(result.n)), "template": result.templates}
    for name in COLUMNS:
        columns[name] = result.columns[name].tolist()
    fixed = {"idx", "template", *COLUMNS}
    collisions = fixed & result.meta.keys()
    if collisions:
        raise ValueError(f"battery meta key(s) collide with fixed parquet columns: {sorted(collisions)}")
    for key, values in result.meta.items():
        columns[key] = values
    pq.write_table(pa.table(columns), parquet_path, compression="zstd", compression_level=9)
    return json_path, parquet_path
