from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ServedCache:
    per_user: Dict[int, set[int]] = field(default_factory=dict)

    def get(self, user_id: int) -> set[int]:
        return self.per_user.setdefault(user_id, set())

    def add(self, user_id: int, post_ids: list[int]):
        self.get(user_id).update(post_ids)


@dataclass
class EmbeddingCache:
    vectors: Dict[int, list[float]] = field(default_factory=dict)
    timestamps: Dict[int, float] = field(default_factory=dict)

    def get(self, post_id: int):
        return self.vectors.get(post_id)

    def set(self, post_id: int, vector: list[float], timestamp: float):
        self.vectors[post_id] = vector
        self.timestamps[post_id] = timestamp


served_cache = ServedCache()
embedding_cache = EmbeddingCache()
