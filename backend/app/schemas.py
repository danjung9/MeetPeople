from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    handle: str
    display_name: str
    bio: str
    avatar_url: str
    persona_type: str

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: int
    author: UserOut
    content: str
    topic: str
    created_at: datetime
    like_count: int
    reply_count: int
    repost_count: int
    quote_count: int
    is_reply: bool
    reply_to_id: int | None

    class Config:
        from_attributes = True


class Explanation(BaseModel):
    score: float
    components: dict[str, float]
    notes: list[str]
    stage_log: list[str] = []
    action_probs: dict[str, float] = {}


class FeedItem(BaseModel):
    post: PostOut
    explanation: Explanation


class FeedResponse(BaseModel):
    items: list[FeedItem]
    generated_at: datetime


class TrendOut(BaseModel):
    topic: str
    score: float


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: int
    handle: str
    persona_type: str


class GraphEdge(BaseModel):
    source: int
    target: int


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
