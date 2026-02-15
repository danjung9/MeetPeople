from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..models import Post, User


@dataclass
class Preferences:
    recency_popularity: float = 0.6
    friends_global: float = 0.5
    niche_viral: float = 0.5
    topic_tech: float = 0.6
    topic_politics: float = 0.3
    topic_culture: float = 0.4

    def topic_weight(self, topic: str) -> float:
        if topic == "tech":
            return self.topic_tech
        if topic == "politics":
            return self.topic_politics
        if topic == "culture":
            return self.topic_culture
        return 0.3


@dataclass
class ScoredPostsQuery:
    user_id: int
    request_time: datetime
    preferences: Preferences
    followee_ids: set[int] = field(default_factory=set)
    engagement_post_ids: list[int] = field(default_factory=list)
    muted_keywords: set[str] = field(default_factory=set)
    served_post_ids: set[int] = field(default_factory=set)


@dataclass
class PostCandidate:
    post: Post
    author: User
    source: str
    is_in_network: bool
    recency: float = 0.0
    popularity: float = 0.0
    topic_match: float = 0.0
    niche_score: float = 0.0
    viral_score: float = 0.0
    action_probs: dict[str, float] = field(default_factory=dict)
    weighted_score: float = 0.0
    diversity_penalty: float = 1.0
    final_score: float = 0.0
    notes: list[str] = field(default_factory=list)
    stage_log: list[str] = field(default_factory=list)

    def add_note(self, note: str):
        if note not in self.notes:
            self.notes.append(note)

    def add_stage(self, stage: str):
        self.stage_log.append(stage)
