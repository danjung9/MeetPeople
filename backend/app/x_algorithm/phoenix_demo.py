from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import os
import numpy as np

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover
    torch = None
    nn = None

from langchain_openai import OpenAIEmbeddings

from .memory import embedding_cache
from ..models import Post


@dataclass
class PhoenixScores:
    like: float
    reply: float
    repost: float
    click: float


class MiniPhoenixModel:
    def __init__(self, seed: int = 42):
        self.seed = seed
        if torch is None:
            self.weights = np.random.default_rng(seed).normal(size=(4, 6))
            self.bias = np.zeros(4)
        else:
            torch.manual_seed(seed)
            self.model = nn.Sequential(
                nn.Linear(6, 12),
                nn.ReLU(),
                nn.Linear(12, 4),
                nn.Sigmoid(),
            )

    def predict(self, features: Iterable[float]) -> PhoenixScores:
        vec = np.array(list(features), dtype=np.float32)
        if torch is None:
            logits = self.weights @ vec + self.bias
            probs = 1 / (1 + np.exp(-logits))
        else:
            with torch.no_grad():
                probs = self.model(torch.tensor(vec)).numpy()
        return PhoenixScores(
            like=float(probs[0]),
            reply=float(probs[1]),
            repost=float(probs[2]),
            click=float(probs[3]),
        )


class PhoenixRetrieval:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedder = OpenAIEmbeddings(model=model) if api_key else None

    def _hash_embed(self, text: str, dim: int = 128) -> list[float]:
        vec = np.zeros(dim, dtype=np.float32)
        for idx, ch in enumerate(text.encode("utf-8")):
            vec[idx % dim] += (ch % 31) * 0.1
        norm = np.linalg.norm(vec) + 1e-6
        return list(vec / norm)

    def _embed(self, text: str) -> list[float]:
        if self.embedder is None:
            return self._hash_embed(text)
        return list(self.embedder.embed_query(text))

    def embed_posts(self, posts: list[Post]) -> dict[int, list[float]]:
        if self.embedder is None:
            return {post.id: self._hash_embed(post.content) for post in posts}
        texts = [p.content for p in posts]
        vectors = self.embedder.embed_documents(texts)
        return {post.id: list(vec) for post, vec in zip(posts, vectors)}

    def get_post_vector(self, post: Post) -> list[float]:
        cached = embedding_cache.get(post.id)
        if cached is not None:
            return cached
        vector = self._embed(post.content)
        embedding_cache.set(post.id, vector, post.created_at.timestamp())
        return vector

    def retrieve(self, user_text: str, candidates: list[Post], top_k: int = 80) -> list[Post]:
        if not candidates:
            return []

        user_vec = np.array(self._embed(user_text), dtype=np.float32)
        user_norm = np.linalg.norm(user_vec) + 1e-6

        scored: list[tuple[float, Post]] = []
        for post in candidates:
            vec = np.array(self.get_post_vector(post), dtype=np.float32)
            score = float(np.dot(user_vec, vec) / (user_norm * (np.linalg.norm(vec) + 1e-6)))
            scored.append((score, post))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [post for _, post in scored[:top_k]]


phoenix_ranker = MiniPhoenixModel()
phoenix_retrieval = PhoenixRetrieval()
