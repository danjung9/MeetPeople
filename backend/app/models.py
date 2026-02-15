from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    handle: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(64))
    bio: Mapped[str] = mapped_column(Text, default="")
    avatar_url: Mapped[str] = mapped_column(String(256), default="")
    persona_type: Mapped[str] = mapped_column(String(32), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author")


class Follow(Base):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    followee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    repost_count: Mapped[int] = mapped_column(Integer, default=0)
    quote_count: Mapped[int] = mapped_column(Integer, default=0)
    is_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_to_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("posts.id"), nullable=True)

    author = relationship("User", back_populates="posts")


class Engagement(Base):
    __tablename__ = "engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), index=True)
    action: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class Trend(Base):
    __tablename__ = "trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(32), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
