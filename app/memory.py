from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.models import MemoryEntry


@dataclass
class MemoryStore:
    """In-memory store with lightweight semantic search via bag-of-words cosine similarity."""

    entries: list[MemoryEntry] = field(default_factory=list)

    def add(self, entry: MemoryEntry) -> None:
        self.entries.append(entry)

    def recent(self, user_id: str, limit: int = 10) -> list[MemoryEntry]:
        candidates = [e for e in self.entries if e.user_id == user_id]
        return candidates[-limit:]

    def semantic_search(self, user_id: str, query: str, limit: int = 5) -> list[MemoryEntry]:
        query_vector = self._vectorize(query)
        scored: list[tuple[float, MemoryEntry]] = []

        for entry in self.entries:
            if entry.user_id != user_id:
                continue
            score = self._cosine(query_vector, self._vectorize(entry.text))
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    @staticmethod
    def _vectorize(text: str) -> Counter[str]:
        tokens = [t.strip(".,!?;:\"'()[]{}").lower() for t in text.split()]
        return Counter(t for t in tokens if t)

    @staticmethod
    def _cosine(a: Counter[str], b: Counter[str]) -> float:
        if not a or not b:
            return 0.0

        dot = sum(a[token] * b.get(token, 0) for token in a)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if not norm_a or not norm_b:
            return 0.0
        return dot / (norm_a * norm_b)


def to_context(entries: list[MemoryEntry]) -> list[dict[str, Any]]:
    return [
        {
            "kind": entry.kind,
            "text": entry.text,
            "metadata": entry.metadata,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in entries
    ]
