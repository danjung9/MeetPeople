"use client";

import { useEffect, useState } from "react";
import { fetchFollowing } from "../lib/api";
import { User } from "../lib/types";

export default function FollowingClient() {
  const [following, setFollowing] = useState<User[]>([]);

  useEffect(() => {
    fetchFollowing(1).then(setFollowing).catch(() => null);
  }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>MeetFriends</h1>
        <a className="nav-item" href="/">Home</a>
        <a className="nav-item" href="/trends">Trends</a>
        <a className="nav-item" href="/notifications">Notifications</a>
        <a className="nav-item" href="/following">Following</a>
        <a className="nav-item" href="/followers">Followers</a>
        <a className="nav-item" href="/graph">Follow Graph</a>
        <a className="nav-item" href="/profile/1">Profile</a>
      </aside>

      <main className="main">
        <section className="card">
          <h2>Following</h2>
          <p className="post-meta">
            These are the people whose posts are treated as in-network for your feed.
          </p>
          {following.length ? (
            following.map((person) => (
              <a key={person.id} className="user-item" href={`/profile/${person.id}`}>
                <strong>{person.display_name}</strong>
                <div className="post-meta">
                  @{person.handle} · {person.persona_type}
                </div>
              </a>
            ))
          ) : (
            <p className="post-meta">Not following anyone yet.</p>
          )}
        </section>
      </main>
    </div>
  );
}
