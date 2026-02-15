"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchFeed, fetchNotifications, fetchTrends, likePost } from "../lib/api";
import { FeedItem, Trend, Notification } from "../lib/types";

const DEFAULTS = {
  recency_popularity: 0.6,
  friends_global: 0.5,
  niche_viral: 0.5,
  topic_tech: 0.6,
  topic_politics: 0.3,
  topic_culture: 0.4,
};

function formatNumber(value: number) {
  return value.toFixed(2);
}

function formatPostDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString();
}

const SIGNAL_LABELS: Record<string, string> = {
  recency: "Recency",
  popularity: "Popularity",
  topic_match: "Topic match",
  in_network: "In network",
  niche: "Niche",
  viral: "Viral",
  diversity: "Diversity",
};

const ACTION_LABELS: Record<string, string> = {
  like: "Like",
  reply: "Reply",
  repost: "Repost",
  click: "Click",
};

export default function HomeClient() {
  const [preferences, setPreferences] = useState(DEFAULTS);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);

  const params = useMemo(
    () => ({ user_id: 1, ...preferences }),
    [preferences]
  );

  async function loadAll() {
    setLoading(true);
    try {
      const data = await fetchFeed(params);
      setFeed(data.items);
      const [trendData, noteData] = await Promise.all([
        fetchTrends(),
        fetchNotifications(1),
      ]);
      setTrends(trendData);
      setNotifications(noteData.slice(0, 6));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, [params]);

  const slider = (key: keyof typeof DEFAULTS, label: string) => (
    <div className="control-row">
      <span>{label}</span>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={preferences[key]}
        onChange={(event) =>
          setPreferences({ ...preferences, [key]: Number(event.target.value) })
        }
      />
      <span className="badge">{formatNumber(preferences[key])}</span>
    </div>
  );

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>MeetFriends</h1>
        <a className="nav-item" href="/">
          Home
          <span className="badge">For You</span>
        </a>
        <a className="nav-item" href="/trends">
          Trends
        </a>
        <a className="nav-item" href="/notifications">
          Notifications
        </a>
        <a className="nav-item" href="/following">
          Following
        </a>
        <a className="nav-item" href="/followers">
          Followers
        </a>
        <a className="nav-item" href="/graph">
          Follow Graph
        </a>
        <a className="nav-item" href="/profile/1">
          Profile
        </a>
      </aside>

      <main className="main">
        <section className="card">
          <div className="feed-header">
            <h2>Home Feed</h2>
          </div>
          <p className="post-meta">
            Tunable feed: recency vs popularity, friends vs global, niche vs viral, and topic focus.
          </p>
          <div className="controls">
            {slider(
              "recency_popularity",
              "Recency vs Popularity"
            )}
            {slider(
              "friends_global",
              "Friends vs Global"
            )}
            {slider(
              "niche_viral",
              "Niche vs Viral"
            )}
            {slider("topic_tech", "Tech Focus")}
            {slider("topic_politics", "Politics Focus")}
            {slider("topic_culture", "Culture Focus")}
          </div>
        </section>

        <section className="card">
          {loading && <p className="post-meta">Refreshing feed...</p>}
          {feed.map((item) => {
            const inNetwork = (item.explanation.components.in_network ?? 0) > 0.5;
            return (
              <article key={item.post.id} className="post">
                <div className="avatar" />
                <div>
                  <div className="post-author">
                    {item.post.author.display_name}
                    <span className="post-meta">@{item.post.author.handle}</span>
                    <span className="badge">{item.post.topic}</span>
                  </div>
                  <div className="post-submeta">
                    <span className={`follow-pill ${inNetwork ? "on" : "off"}`}>
                      {inNetwork ? "Following" : "Not following"}
                    </span>
                    <span className="post-meta">{formatPostDate(item.post.created_at)}</span>
                  </div>
                  <p className="post-content">{item.post.content}</p>
                  <div className="post-actions">
                    <button
                      className="post-action"
                      onClick={() => likePost(item.post.id).then(loadAll).catch(() => null)}
                    >
                      Like {item.post.like_count}
                    </button>
                    <span>Replies {item.post.reply_count}</span>
                    <span>Reposts {item.post.repost_count}</span>
                  </div>
                  <div className="explain">
                    <div className="explain-header">
                      <strong>Why this is here</strong>
                      <span className="badge">Score {item.explanation.score.toFixed(3)}</span>
                    </div>

                    <div className="explain-section-title">Signals</div>
                    <div className="explain-grid">
                      {Object.entries(item.explanation.components).map(([key, value]) => {
                        const label = SIGNAL_LABELS[key] ?? key;
                        const display =
                          key === "in_network" ? (value > 0.5 ? "Yes" : "No") : value.toFixed(2);
                        return (
                          <div key={key} className="explain-chip">
                            <span>{label}</span>
                            <strong>{display}</strong>
                          </div>
                        );
                      })}
                    </div>

                    <div className="explain-section-title">Action probabilities</div>
                    <div className="explain-grid">
                      {Object.entries(item.explanation.action_probs || {}).map(([key, value]) => (
                        <div key={key} className="explain-chip">
                          <span>{ACTION_LABELS[key] ?? key}</span>
                          <strong>{value.toFixed(2)}</strong>
                        </div>
                      ))}
                    </div>

                    <div className="explain-notes">
                      {item.explanation.notes.length
                        ? item.explanation.notes.map((note) => (
                            <span key={note} className="note-pill">
                              {note}
                            </span>
                          ))
                        : "Balanced across preferences"}
                    </div>

                    <div className="explain-pipeline">
                      {item.explanation.stage_log?.length
                        ? `Pipeline: ${item.explanation.stage_log.join(" → ")}`
                        : "Pipeline: hydration → sources → filters → scorers → selection"}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      </main>

      <aside className="sidebar right-rail">
        <div className="card" style={{ marginBottom: 16 }}>
          <h3>Trends</h3>
          {trends.map((trend) => (
            <div key={trend.topic} className="trend-item">
              <strong>{trend.topic}</strong>
              <div className="post-meta">Score {trend.score.toFixed(0)}</div>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Notifications</h3>
          {notifications.map((note) => (
            <div key={note.id} className="notification-item">
              <strong>{note.title}</strong>
              <div className="post-meta">{note.body}</div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
