from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from ..models import Post, Trend


def update_trends(db: Session):
    stmt = (
        select(Post.topic, func.count(Post.id))
        .group_by(Post.topic)
        .order_by(desc(func.count(Post.id)))
    )
    results = list(db.execute(stmt))

    db.query(Trend).delete()
    for topic, count in results:
        db.add(Trend(topic=topic, score=float(count)))
    db.commit()
