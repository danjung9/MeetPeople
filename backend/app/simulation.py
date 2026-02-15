from __future__ import annotations

import random
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import User, Post, Engagement, Notification, Follow
from .llm import PersonaSpec, generate_post, generate_reply

TOPICS = ["tech", "politics", "culture"]
ACTIONS = ["like", "reply", "repost"]


def choose_topic(persona: PersonaSpec) -> str:
    if persona.topics:
        return random.choice(persona.topics)
    return random.choice(TOPICS)


def create_post(db: Session, persona: PersonaSpec, content: str, topic: str) -> Post:
    user = db.scalar(select(User).where(User.handle == persona.handle))
    if user is None:
        raise ValueError("Persona not found")
    post = Post(author_id=user.id, content=content, topic=topic)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def simulate_engagement(db: Session, user: User, post: Post, action: str):
    engagement = Engagement(user_id=user.id, post_id=post.id, action=action)
    if action == "like":
        post.like_count += 1
    elif action == "reply":
        post.reply_count += 1
    elif action == "repost":
        post.repost_count += 1

    db.add(engagement)
    db.add(post)
    db.add(
        Notification(
            user_id=post.author_id,
            title=f"New {action}",
            body=f"@{user.handle} {action}ed your post.",
        )
    )
    db.commit()


def simulate_step(db: Session, personas: list[PersonaSpec], llm=None):
    persona = random.choice(personas)
    topic = choose_topic(persona)
    content = generate_post(llm, persona, topic)
    post = create_post(db, persona, content, topic)

    other_users = list(db.scalars(select(User).where(User.handle != persona.handle)))
    if other_users:
        for _ in range(random.randint(1, 3)):
            engager = random.choice(other_users)
            action = random.choice(ACTIONS)
            simulate_engagement(db, engager, post, action)

    if random.random() < 0.25 and other_users:
        replier = random.choice(other_users)
        reply_persona = next((p for p in personas if p.handle == replier.handle), None)
        if reply_persona:
            reply_content = generate_reply(llm, reply_persona, post.content)
            reply_post = Post(
                author_id=replier.id,
                content=reply_content,
                topic=post.topic,
                is_reply=True,
                reply_to_id=post.id,
                created_at=datetime.utcnow(),
            )
            db.add(reply_post)
            db.commit()


def ensure_follows(db: Session, users: list[User]):
    existing = {(f.follower_id, f.followee_id) for f in db.scalars(select(Follow))}
    for user in users:
        choices = [u for u in users if u.id != user.id]
        random.shuffle(choices)
        for followee in choices[: random.randint(2, min(6, len(choices)) )]:
            key = (user.id, followee.id)
            if key in existing:
                continue
            db.add(Follow(follower_id=user.id, followee_id=followee.id))
            existing.add(key)
    db.commit()
