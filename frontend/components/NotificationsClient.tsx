"use client";

import { useEffect, useState } from "react";
import { fetchNotifications } from "../lib/api";
import { Notification } from "../lib/types";

export default function NotificationsClient() {
  const [notes, setNotes] = useState<Notification[]>([]);

  useEffect(() => {
    fetchNotifications(1).then(setNotes).catch(() => null);
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
          <h2>Notifications</h2>
          {notes.map((note) => (
            <div key={note.id} className="notification-item">
              <strong>{note.title}</strong>
              <div className="post-meta">{note.body}</div>
              <div className="post-meta">
                {new Date(note.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
