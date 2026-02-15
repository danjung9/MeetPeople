from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import exp, log1p

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .memory import served_cache
from ..models import Post, Follow, Engagement, User
from .phoenix_demo import phoenix_ranker, phoenix_retrieval
from .pipeline_framework import (
    CandidatePipeline,
    StageLog,
    QueryHydrator,
    Source,
    Hydrator,
    Filter,
    Scorer,
    Selector,
    SideEffect,
)
from .pipeline_types import ScoredPostsQuery, PostCandidate


HALF_LIFE_HOURS = 12.0
RETENTION_DAYS = 7


def _recency_score(created_at: datetime, now: datetime) -> float:
    age_hours = max((now - created_at).total_seconds() / 3600.0, 0.0)
    return exp(-age_hours / HALF_LIFE_HOURS)


def _popularity_score(post: Post) -> float:
    return log1p(post.like_count + post.reply_count * 1.5 + post.repost_count * 2.0)


class UserActionSeqQueryHydrator(QueryHydrator[ScoredPostsQuery]):
    def __init__(self, db: Session):
        self.db = db

    def hydrate(self, query: ScoredPostsQuery) -> StageLog | None:
        stmt = (
            select(Engagement)
            .where(Engagement.user_id == query.user_id)
            .order_by(desc(Engagement.created_at))
            .limit(50)
        )
        engagements = list(self.db.scalars(stmt))
        query.engagement_post_ids = [e.post_id for e in engagements]
        return StageLog(stage="query_hydration", detail=f"Loaded {len(engagements)} recent engagements")


class UserFeaturesQueryHydrator(QueryHydrator[ScoredPostsQuery]):
    def __init__(self, db: Session):
        self.db = db

    def hydrate(self, query: ScoredPostsQuery) -> StageLog | None:
        followees = set(
            self.db.scalars(select(Follow.followee_id).where(Follow.follower_id == query.user_id))
        )
        query.followee_ids = followees
        query.served_post_ids = served_cache.get(query.user_id)
        return StageLog(stage="query_hydration", detail=f"Loaded {len(followees)} followees")


class ThunderSource(Source[ScoredPostsQuery, PostCandidate]):
    def __init__(self, db: Session):
        self.db = db

    def fetch(self, query: ScoredPostsQuery) -> list[PostCandidate]:
        if not query.followee_ids:
            return []
        stmt = (
            select(Post)
            .where(Post.author_id.in_(query.followee_ids))
            .order_by(desc(Post.created_at))
            .limit(300)
        )
        posts = list(self.db.scalars(stmt))
        return [
            PostCandidate(
                post=post,
                author=post.author,
                source="thunder",
                is_in_network=True,
            )
            for post in posts
        ]


class PhoenixSource(Source[ScoredPostsQuery, PostCandidate]):
    def __init__(self, db: Session):
        self.db = db

    def fetch(self, query: ScoredPostsQuery) -> list[PostCandidate]:
        stmt = select(Post).order_by(desc(Post.created_at)).limit(800)
        posts = [post for post in self.db.scalars(stmt) if post.author_id not in query.followee_ids]

        user_text = " ".join(
            post.content
            for post in self.db.scalars(select(Post).where(Post.id.in_(query.engagement_post_ids)))
        )
        if not user_text:
            user_text = "feed exploration"

        retrieved = phoenix_retrieval.retrieve(user_text, posts, top_k=150)
        return [
            PostCandidate(
                post=post,
                author=post.author,
                source="phoenix",
                is_in_network=False,
            )
            for post in retrieved
        ]


class CoreDataCandidateHydrator(Hydrator[ScoredPostsQuery, PostCandidate]):
    def hydrate(self, query: ScoredPostsQuery, candidates: list[PostCandidate]) -> StageLog | None:
        for candidate in candidates:
            candidate.add_stage("core_data")
        return StageLog(stage="candidate_hydration", detail=f"Hydrated {len(candidates)} candidates")


class AgeFilter(Filter[ScoredPostsQuery, PostCandidate]):
    def filter(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        cutoff = query.request_time - timedelta(days=RETENTION_DAYS)
        kept = [c for c in candidates if c.post.created_at >= cutoff]
        return kept, StageLog(stage="filter", detail=f"Age filter removed {len(candidates) - len(kept)}")


class SelfTweetFilter(Filter[ScoredPostsQuery, PostCandidate]):
    def filter(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        kept = [c for c in candidates if c.post.author_id != query.user_id]
        return kept, StageLog(stage="filter", detail=f"Self filter removed {len(candidates) - len(kept)}")


class DropDuplicatesFilter(Filter[ScoredPostsQuery, PostCandidate]):
    def filter(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        seen = set()
        unique: list[PostCandidate] = []
        for candidate in candidates:
            if candidate.post.id in seen:
                continue
            seen.add(candidate.post.id)
            unique.append(candidate)
        return unique, StageLog(stage="filter", detail=f"Deduped to {len(unique)} candidates")


class PreviouslySeenPostsFilter(Filter[ScoredPostsQuery, PostCandidate]):
    def filter(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        seen = set(query.engagement_post_ids) | set(query.served_post_ids)
        kept = [c for c in candidates if c.post.id not in seen]
        return kept, StageLog(stage="filter", detail=f"Removed {len(candidates) - len(kept)} seen posts")


class PhoenixScorer(Scorer[ScoredPostsQuery, PostCandidate]):
    def score(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        if not candidates:
            return StageLog(stage="scorer", detail="No candidates to score")
        max_popularity = max((_popularity_score(c.post) for c in candidates), default=1.0)
        popularity_scale = max_popularity if max_popularity > 0.0 else 1.0

        for candidate in candidates:
            candidate.recency = _recency_score(candidate.post.created_at, query.request_time)
            candidate.popularity = min(_popularity_score(candidate.post) / popularity_scale, 1.0)
            candidate.topic_match = query.preferences.topic_weight(candidate.post.topic)
            candidate.niche_score = 1.0 - candidate.popularity
            candidate.viral_score = candidate.popularity

            features = [
                candidate.recency,
                candidate.popularity,
                candidate.topic_match,
                1.0 if candidate.is_in_network else 0.0,
                candidate.niche_score,
                candidate.viral_score,
            ]
            probs = phoenix_ranker.predict(features)
            candidate.action_probs = {
                "like": probs.like,
                "reply": probs.reply,
                "repost": probs.repost,
                "click": probs.click,
            }

            if candidate.is_in_network:
                candidate.add_note("From someone you follow")
            if candidate.recency > 0.7:
                candidate.add_note("Fresh post")
            if candidate.popularity > 0.6:
                candidate.add_note("High engagement velocity")
            if candidate.topic_match > 0.6:
                candidate.add_note(f"Matches your {candidate.post.topic} interest")

        return StageLog(stage="scorer", detail=f"Phoenix scored {len(candidates)} candidates")


class WeightedScorer(Scorer[ScoredPostsQuery, PostCandidate]):
    def score(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        weights = {
            "like": 0.4,
            "reply": 0.3,
            "repost": 0.2,
            "click": 0.1,
        }
        for candidate in candidates:
            weighted = sum(candidate.action_probs.get(k, 0.0) * v for k, v in weights.items())
            recency_mix = candidate.recency * query.preferences.recency_popularity
            popularity_mix = candidate.popularity * (1.0 - query.preferences.recency_popularity)
            network_mix = (1.0 if candidate.is_in_network else 0.0) * query.preferences.friends_global
            global_mix = (1.0 if not candidate.is_in_network else 0.0) * (1.0 - query.preferences.friends_global)
            niche_mix = candidate.niche_score * query.preferences.niche_viral
            viral_mix = candidate.viral_score * (1.0 - query.preferences.niche_viral)

            candidate.weighted_score = (
                weighted
                + recency_mix
                + popularity_mix
                + candidate.topic_match
                + network_mix
                + global_mix
                + niche_mix
                + viral_mix
            )
        return StageLog(stage="scorer", detail="Weighted scorer combined action probabilities")


class AuthorDiversityScorer(Scorer[ScoredPostsQuery, PostCandidate]):
    def score(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        counts: dict[int, int] = {}
        for candidate in candidates:
            count = counts.get(candidate.author.id, 0)
            candidate.diversity_penalty = 0.85**count
            candidate.final_score = candidate.weighted_score * candidate.diversity_penalty
            counts[candidate.author.id] = count + 1
            if candidate.diversity_penalty < 0.9:
                candidate.add_note("Adjusted for author diversity")
        return StageLog(stage="scorer", detail="Author diversity penalty applied")


class TopKScoreSelector(Selector[ScoredPostsQuery, PostCandidate]):
    def __init__(self, k: int = 50):
        self.k = k

    def select(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        candidates.sort(key=lambda c: c.final_score, reverse=True)
        selected = candidates[: self.k]
        return selected, StageLog(stage="selector", detail=f"Selected top {len(selected)}")


class DedupConversationFilter(Filter[ScoredPostsQuery, PostCandidate]):
    def filter(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        seen_reply: set[int] = set()
        kept: list[PostCandidate] = []
        for candidate in candidates:
            reply_to = candidate.post.reply_to_id
            if reply_to and reply_to in seen_reply:
                continue
            if reply_to:
                seen_reply.add(reply_to)
            kept.append(candidate)
        return kept, StageLog(stage="post_filter", detail="Conversation dedup applied")


class CacheRequestInfoSideEffect(SideEffect[ScoredPostsQuery, PostCandidate]):
    def run(self, query: ScoredPostsQuery, candidates: list[PostCandidate]):
        served_cache.add(query.user_id, [c.post.id for c in candidates])
        return StageLog(stage="side_effect", detail="Cached served post ids")


@dataclass
class XPipeline:
    db: Session

    def build(self) -> CandidatePipeline[ScoredPostsQuery, PostCandidate]:
        return CandidatePipeline(
            query_hydrators=[UserActionSeqQueryHydrator(self.db), UserFeaturesQueryHydrator(self.db)],
            sources=[ThunderSource(self.db), PhoenixSource(self.db)],
            candidate_hydrators=[CoreDataCandidateHydrator()],
            filters=[AgeFilter(), SelfTweetFilter(), DropDuplicatesFilter()],
            scorers=[PhoenixScorer(), WeightedScorer(), AuthorDiversityScorer()],
            selector=TopKScoreSelector(k=60),
            post_filters=[DedupConversationFilter()],
            side_effects=[],
        )
