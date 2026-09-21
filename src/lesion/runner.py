"""Drives one run: pairs -> grouped batches -> clean and intervened passes -> per-prompt metrics -> aggregates."""

from __future__ import annotations

from collections import defaultdict


def group_by_length(id_lists, batch_size: int) -> list[list[int]]:
    """Batches of indices whose token sequences share a length, so no padding or
    attention mask exists (E0's trick). Lengths ascending, index order within a
    length, then chunks of ``batch_size``. Identical to E0's iteration order."""
    groups: dict[int, list[int]] = defaultdict(list)
    for i, ids in enumerate(id_lists):
        groups[len(ids)].append(i)
    batches = []
    for length in sorted(groups):
        idxs = groups[length]
        for start in range(0, len(idxs), batch_size):
            batches.append(idxs[start:start + batch_size])
    return batches
