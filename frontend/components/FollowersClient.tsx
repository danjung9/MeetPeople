"use client";

import { useEffect, useState } from "react";
import { fetchFollowers } from "../lib/api";
import { User } from "../lib/types";

export default function FollowersClient() {
  const [followers, setFollowers] = useState<User[]>([]);

  useEffect(() => {
    fetchFollowers(1).then(setFollowers).catch(() => null);
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
          <h2>Followers</h2>
          <p className="post-meta">
            People who follow you. Helpful for understanding who amplifies your posts.
          </p>
          {followers.length ? (
            followers.map((person) => (
              <a key={person.id} className="user-item" href={`/profile/${person.id}`}>
                <strong>{person.display_name}</strong>
                <div className="post-meta">
                  @{person.handle} · {person.persona_type}
                </div>
              </a>
            ))
          ) : (
            <p className="post-meta">No followers yet.</p>
          )}
        </section>
      </main>
    </div>
  );
}
