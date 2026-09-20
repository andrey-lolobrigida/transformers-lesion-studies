"""The interface between a task battery and the harness: clean/corrupt prompt
pairs whose token sequences align position by position, plus a structured
description of the corruption (O-003 resolution, item 1).

E1a ships one battery (IOI, ``ioi.py``). E1b adds the others behind the same
protocol; the metric stays fixed at logit difference at ``positions["END"]``
until E1b has a written reason to change it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


class AlignmentError(ValueError):
    """Tokenisation misalignment. A hard stop, never a warning."""


@dataclass(frozen=True)
class Corruption:
    name: str  # e.g. "p_ABC"
    removes: str  # what information the corruption takes away
    inserts: str  # what it puts in its place
    source: str  # citation, e.g. "wang-2022 §2.1"


@dataclass(frozen=True)
class PromptPair:
    clean_ids: tuple[int, ...]
    corrupt_ids: tuple[int, ...]  # same length as clean_ids, always
    answer_id: int  # c, the correct token
    competitor_id: int  # s, the named competitor
    positions: Mapping[str, int]  # label -> index on the clean prompt, e.g. END, S1, S1+1, S2, IO
    corrupt_positions: Mapping[str, int]  # the same labels on the corrupt prompt
    template: str  # e.g. "BABA/3"; matched mean references group on it
    meta: Mapping[str, str]  # free, written to parquet as string columns

    def __post_init__(self) -> None:
        n = len(self.clean_ids)
        if len(self.corrupt_ids) != n:
            raise AlignmentError(f"clean has {n} tokens, corrupt has {len(self.corrupt_ids)}")
        if set(self.positions) != set(self.corrupt_positions):
            raise AlignmentError(
                f"label sets differ: {sorted(self.positions)} vs {sorted(self.corrupt_positions)}"
            )
        if "END" not in self.positions:
            raise AlignmentError("every pair needs an END label (where the logits are read)")
        for side in (self.positions, self.corrupt_positions):
            for label, i in side.items():
                if not 0 <= i < n:
                    raise AlignmentError(f"label {label!r} -> {i} out of range for {n} tokens")


class Battery(Protocol):
    name: str
    corruption: Corruption
    labels: tuple[str, ...]  # every position label a PromptPair from this battery carries
    template_set: str  # human-readable description, written to the artifact

    def pairs(self, n: int, seed: int, prepend_bos: bool) -> list[PromptPair]: ...


def encode(tokenizer, text: str) -> list[int]:
    """Token ids with no special tokens. Asserts the tokenizer did not prepend
    BOS anyway (the TransformerLens gotcha, docs/06-environment.md)."""
    ids = list(tokenizer(text, add_special_tokens=False).input_ids)
    if ids and ids[0] == tokenizer.bos_token_id:
        raise AlignmentError("plain tokenizer prepended BOS unexpectedly")
    return ids


def with_bos(ids: list[int], positions: Mapping[str, int], bos_id: int) -> tuple[list[int], dict[str, int]]:
    """Prepend BOS and shift every label index by one."""
    return [bos_id, *ids], {label: i + 1 for label, i in positions.items()}
