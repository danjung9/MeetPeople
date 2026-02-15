from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy import select

from .db import Base, engine, SessionLocal
from .models import User, Post, Engagement
from .llm import DEFAULT_PERSONAS, get_llm, PersonaSpec, generate_post
from .simulation import ensure_follows

TARGET_USER_COUNT = 35
MIN_POSTS_PER_USER = 8
MAX_POSTS_PER_USER = 14
TARGET_ENGAGEMENTS = 32

FIRST_NAMES = [
    "Avery",
    "Jordan",
    "Riley",
    "Quinn",
    "Maya",
    "Eli",
    "Sofia",
    "Noah",
    "Ari",
    "Zoe",
    "Kai",
    "Milo",
    "Leah",
    "Iris",
    "Owen",
]

LAST_NAMES = [
    "Nguyen",
    "Carter",
    "Singh",
    "Ramirez",
    "Khan",
    "Park",
    "Lopez",
    "Hughes",
    "Ali",
    "Kim",
    "Patel",
    "Brooks",
    "Bennett",
    "Rivera",
    "Moreno",
]

PERSONA_TYPES = [
    "builder",
    "analyst",
    "creator",
    "critic",
    "operator",
    "scientist",
    "economist",
    "producer",
    "writer",
    "strategist",
    "researcher",
    "maker",
]

PERSONA_TOPICS: dict[str, list[str]] = {
    "builder": ["tech"],
    "analyst": ["tech", "politics"],
    "creator": ["culture", "tech"],
    "critic": ["culture"],
    "operator": ["tech"],
    "scientist": ["tech", "politics"],
    "economist": ["politics", "tech"],
    "producer": ["culture"],
    "writer": ["culture", "politics"],
    "strategist": ["tech", "politics"],
    "researcher": ["tech"],
    "maker": ["tech", "culture"],
}

PERSONA_BIOS: dict[str, str] = {
    "builder": "Shipping software, systems, and calm execution.",
    "analyst": "Trends, numbers, and what the data actually says.",
    "creator": "Making things people feel, share, and remix.",
    "critic": "Culture notes, media deep dives, sharp takes.",
    "operator": "Operational clarity, reliable delivery, fewer surprises.",
    "scientist": "Methodical, skeptical, and curious about the why.",
    "economist": "Markets, policy, and incentives that shape outcomes.",
    "producer": "Story structure, pacing, and production craft.",
    "writer": "Threads with angles, narratives, and receipts.",
    "strategist": "Positioning, differentiation, and long-term bets.",
    "researcher": "Exploration over certainty; references welcome.",
    "maker": "Prototyping fast and learning in public.",
}


def stable_target_posts(handle: str) -> int:
    rng = random.Random(sum(ord(ch) for ch in handle))
    return rng.randint(MIN_POSTS_PER_USER, MAX_POSTS_PER_USER)


def generate_unique_handle(existing: set[str]) -> str:
    for _ in range(50):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        base = f"{first[0]}{last}".lower()
        handle = base
        if handle not in existing:
            return handle
        handle = f"{base}{random.randint(2, 99)}"
        if handle not in existing:
            return handle
    return f"user{random.randint(100, 999)}"


def random_recent_timestamp(days: int = 7) -> datetime:
    now = datetime.datetime.now(datetime.UTC)
    hours = random.randint(0, days * 24)
    minutes = random.randint(0, 59)
    return now - timedelta(hours=hours, minutes=minutes)


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_users = list(db.scalars(select(User)))
        existing_handles = {user.handle for user in existing_users}

        if "you" not in existing_handles:
            demo_user = User(
                handle="you",
                display_name="Demo User",
                bio="Tuning my feed in real time.",
                avatar_url="",
                persona_type="viewer",
            )
            db.add(demo_user)

        personas: list[PersonaSpec] = list(DEFAULT_PERSONAS)
        for persona in personas:
            if persona.handle in existing_handles:
                continue
            db.add(
                User(
                    handle=persona.handle,
                    display_name=persona.display_name,
                    bio=persona.bio,
                    avatar_url="",
                    persona_type=persona.persona_type,
                )
            )
        db.commit()

        users = list(db.scalars(select(User)))
        existing_handles = {user.handle for user in users}
        extra_needed = max(0, TARGET_USER_COUNT - len(users))
        generated_personas: list[PersonaSpec] = []
        for _ in range(extra_needed):
            handle = generate_unique_handle(existing_handles)
            existing_handles.add(handle)
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            persona_type = random.choice(PERSONA_TYPES)
            topics = PERSONA_TOPICS.get(persona_type, ["tech", "culture", "politics"])
            bio = PERSONA_BIOS.get(persona_type, "Exploring ideas and shipping experiments.")
            display_name = f"{first} {last}"
            generated_personas.append(
                PersonaSpec(
                    handle=handle,
                    display_name=display_name,
                    bio=bio,
                    persona_type=persona_type,
                    topics=topics,
                    style_notes="concise, thoughtful, and conversational",
                )
            )

        for persona in generated_personas:
            db.add(
                User(
                    handle=persona.handle,
                    display_name=persona.display_name,
                    bio=persona.bio,
                    avatar_url="",
                    persona_type=persona.persona_type,
                )
            )
        db.commit()
        personas.extend(generated_personas)

        users = list(db.scalars(select(User)))
        ensure_follows(db, users)

        llm = get_llm()
        handle_to_user = {user.handle: user for user in users}
        for persona in personas:
            author = handle_to_user.get(persona.handle)
            if not author:
                continue
            existing_posts = list(db.scalars(select(Post).where(Post.author_id == author.id)))
            target_posts = stable_target_posts(persona.handle)
            for _ in range(max(0, target_posts - len(existing_posts))):
                topic = random.choice(persona.topics or ["tech", "politics", "culture"])
                content = generate_post(llm, persona, topic)
                db.add(
                    Post(
                        author_id=author.id,
                        content=content,
                        topic=topic,
                        created_at=random_recent_timestamp(),
                    )
                )
        db.commit()

        demo = handle_to_user.get("you")
        if demo:
            demo_topics = ["tech", "culture", "politics"]
            demo_existing = list(db.scalars(select(Post).where(Post.author_id == demo.id)))
            for index in range(max(0, 3 - len(demo_existing))):
                topic = demo_topics[index % len(demo_topics)]
                db.add(
                    Post(
                        author_id=demo.id,
                        content=f"[viewer] Demo User: tuning my feed with a {topic} focus today.",
                        topic=topic,
                        created_at=random_recent_timestamp(days=2),
                    )
                )
            db.commit()

        demo = handle_to_user.get("you")
        if demo:
            all_posts = list(db.scalars(select(Post)))
            existing_engagements = list(db.scalars(select(Engagement).where(Engagement.user_id == demo.id)))
            target_engagements = TARGET_ENGAGEMENTS
            needed = max(0, target_engagements - len(existing_engagements))
            if all_posts and needed > 0:
                for post in random.sample(all_posts, k=min(needed, len(all_posts))):
                    db.add(
                        Engagement(
                            user_id=demo.id,
                            post_id=post.id,
                            action=random.choice(["like", "reply", "repost"]),
                        )
                    )
                db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
