"use client";

import { useEffect, useState } from "react";
import { fetchTrends } from "../lib/api";
import { Trend } from "../lib/types";

export default function TrendsClient() {
  const [trends, setTrends] = useState<Trend[]>([]);

  useEffect(() => {
    fetchTrends().then(setTrends).catch(() => null);
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
          <h2>Trends</h2>
          {trends.map((trend) => (
            <div key={trend.topic} className="trend-item">
              <strong>{trend.topic}</strong>
              <div className="post-meta">Score {trend.score.toFixed(0)}</div>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
