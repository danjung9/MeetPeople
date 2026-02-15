from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from .db import Base, engine, get_db
from .models import User, Post, Notification, Trend, Follow, Engagement
from .schemas import FeedResponse, FeedItem, Explanation, UserOut, PostOut, TrendOut, NotificationOut, GraphOut, GraphNode, GraphEdge
from .x_algorithm.pipeline_types import Preferences, ScoredPostsQuery
from .x_algorithm.x_pipeline import XPipeline
from .x_algorithm.pipeline import update_trends
from .simulation import simulate_step
from .llm import DEFAULT_PERSONAS, get_llm

Base.metadata.create_all(bind=engine)

app = FastAPI(title="X Recommend Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/users", response_model=list[UserOut])
async def list_users(db: Session = Depends(get_db)):
    users = list(db.scalars(select(User).order_by(User.id)))
    return [UserOut.model_validate(user) for user in users]


@app.get("/feed", response_model=FeedResponse)
async def feed(
    user_id: int = 1,
    recency_popularity: float = 0.6,
    friends_global: float = 0.5,
    niche_viral: float = 0.5,
    topic_tech: float = 0.6,
    topic_politics: float = 0.3,
    topic_culture: float = 0.4,
    db: Session = Depends(get_db),
):
    prefs = Preferences(
        recency_popularity=recency_popularity,
        friends_global=friends_global,
        niche_viral=niche_viral,
        topic_tech=topic_tech,
        topic_politics=topic_politics,
        topic_culture=topic_culture,
    )

    query = ScoredPostsQuery(user_id=user_id, request_time=datetime.utcnow(), preferences=prefs)
    pipeline = XPipeline(db).build()
    result = pipeline.run(query)

    items: list[FeedItem] = []
    stage_log = [log.stage for log in result.logs]
    for candidate in result.candidates:
        post = candidate.post
        items.append(
            FeedItem(
                post=PostOut(
                    id=post.id,
                    author=UserOut.model_validate(post.author),
                    content=post.content,
                    topic=post.topic,
                    created_at=post.created_at,
                    like_count=post.like_count,
                    reply_count=post.reply_count,
                    repost_count=post.repost_count,
                    quote_count=post.quote_count,
                    is_reply=post.is_reply,
                    reply_to_id=post.reply_to_id,
                ),
                explanation=Explanation(
                    score=candidate.final_score,
                    components={
                        "recency": candidate.recency,
                        "popularity": candidate.popularity,
                        "topic_match": candidate.topic_match,
                        "in_network": 1.0 if candidate.is_in_network else 0.0,
                        "niche": candidate.niche_score,
                        "viral": candidate.viral_score,
                        "diversity": candidate.diversity_penalty,
                    },
                    notes=candidate.notes,
                    stage_log=stage_log,
                    action_probs=candidate.action_probs,
                ),
            )
        )

    return FeedResponse(items=items, generated_at=datetime.utcnow())


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    return UserOut.model_validate(user)


@app.get("/users/{user_id}/posts", response_model=list[PostOut])
async def get_user_posts(user_id: int, db: Session = Depends(get_db)):
    stmt = select(Post).where(Post.author_id == user_id).order_by(desc(Post.created_at))
    posts = list(db.scalars(stmt))
    return [
        PostOut(
            id=post.id,
            author=UserOut.model_validate(post.author),
            content=post.content,
            topic=post.topic,
            created_at=post.created_at,
            like_count=post.like_count,
            reply_count=post.reply_count,
            repost_count=post.repost_count,
            quote_count=post.quote_count,
            is_reply=post.is_reply,
            reply_to_id=post.reply_to_id,
        )
        for post in posts
    ]


@app.post("/posts/{post_id}/like")
async def like_post(post_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    liker = db.get(User, user_id)
    post.like_count += 1
    db.add(Engagement(user_id=user_id, post_id=post.id, action="like"))
    if post.author_id != user_id:
        handle = liker.handle if liker else f"user {user_id}"
        db.add(
            Notification(
                user_id=post.author_id,
                title="New like",
                body=f"@{handle} liked your post.",
            )
        )
    db.add(post)
    db.commit()
    return {"status": "ok", "like_count": post.like_count}


@app.get("/users/{user_id}/followers", response_model=list[UserOut])
async def get_user_followers(user_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.followee_id == user_id)
        .order_by(desc(Follow.created_at))
    )
    users = list(db.scalars(stmt))
    return [UserOut.model_validate(user) for user in users]


@app.get("/users/{user_id}/following", response_model=list[UserOut])
async def get_user_following(user_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(User)
        .join(Follow, Follow.followee_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(desc(Follow.created_at))
    )
    users = list(db.scalars(stmt))
    return [UserOut.model_validate(user) for user in users]


@app.get("/trends", response_model=list[TrendOut])
async def trends(db: Session = Depends(get_db)):
    update_trends(db)
    stmt = select(Trend).order_by(desc(Trend.score))
    return [TrendOut(topic=trend.topic, score=trend.score) for trend in db.scalars(stmt)]


@app.get("/notifications", response_model=list[NotificationOut])
async def notifications(user_id: int = 1, db: Session = Depends(get_db)):
    stmt = select(Notification).where(Notification.user_id == user_id).order_by(desc(Notification.created_at))
    notes = list(db.scalars(stmt))
    return [NotificationOut.model_validate(note) for note in notes]


@app.get("/graph", response_model=GraphOut)
async def follow_graph(db: Session = Depends(get_db)):
    users = list(db.scalars(select(User)))
    edges = list(db.scalars(select(Follow)))
    return GraphOut(
        nodes=[GraphNode(id=user.id, handle=user.handle, persona_type=user.persona_type) for user in users],
        edges=[GraphEdge(source=edge.follower_id, target=edge.followee_id) for edge in edges],
    )


@app.post("/simulate/step")
async def simulate(steps: int = 1, db: Session = Depends(get_db)):
    llm = get_llm()
    for _ in range(max(1, steps)):
        simulate_step(db, DEFAULT_PERSONAS, llm=llm)
    update_trends(db)
    return {"status": "ok", "steps": steps}
