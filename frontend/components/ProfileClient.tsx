"use client";

import { useEffect, useState } from "react";
import { fetchFollowers, fetchFollowing, fetchUser, fetchUserPosts, fetchUsers, likePost } from "../lib/api";
import { Post, User } from "../lib/types";

function formatPostDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString();
}

export default function ProfileClient({ userId }: { userId: number }) {
  const [user, setUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [followers, setFollowers] = useState<User[]>([]);
  const [following, setFollowing] = useState<User[]>([]);
  const [viewerFollowing, setViewerFollowing] = useState<User[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [connectionView, setConnectionView] = useState<"following" | "not_following">("following");

  useEffect(() => {
    fetchUser(userId).then(setUser).catch(() => null);
    fetchUserPosts(userId).then(setPosts).catch(() => null);
    fetchFollowers(userId).then(setFollowers).catch(() => null);
    fetchFollowing(userId).then(setFollowing).catch(() => null);
    fetchFollowing(1).then(setViewerFollowing).catch(() => null);
    fetchUsers().then(setAllUsers).catch(() => null);
  }, [userId]);

  const followingIds = new Set(following.map((followee) => followee.id));
  const viewerFollowingIds = new Set(viewerFollowing.map((followee) => followee.id));
  const notFollowing = allUsers.filter(
    (candidate) => candidate.id !== userId && !followingIds.has(candidate.id)
  );
  const connectionList = connectionView === "following" ? following : notFollowing;
  const sidebarFollowing = following.slice(0, 6);
  const sidebarFollowers = followers.slice(0, 6);

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
        <a className="nav-item" href={`/profile/${userId}`}>Profile</a>

        <div className="sidebar-section">
          <div className="sidebar-title-row">
            <h3>Following</h3>
            <span className="badge">{following.length}</span>
          </div>
          {sidebarFollowing.length ? (
            sidebarFollowing.map((person) => (
              <a key={person.id} className="sidebar-user" href={`/profile/${person.id}`}>
                <strong>{person.display_name}</strong>
                <span className="post-meta">@{person.handle}</span>
              </a>
            ))
          ) : (
            <p className="post-meta">Not following anyone yet.</p>
          )}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-title-row">
            <h3>Followers</h3>
            <span className="badge">{followers.length}</span>
          </div>
          {sidebarFollowers.length ? (
            sidebarFollowers.map((person) => (
              <a key={person.id} className="sidebar-user" href={`/profile/${person.id}`}>
                <strong>{person.display_name}</strong>
                <span className="post-meta">@{person.handle}</span>
              </a>
            ))
          ) : (
            <p className="post-meta">No followers yet.</p>
          )}
        </div>
      </aside>

      <main className="main">
        <section className="card">
          <h2>{user?.display_name}</h2>
          <p className="post-meta">@{user?.handle}</p>
          <p>{user?.bio}</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <span className="badge">{user?.persona_type}</span>
            <span className="badge">{followers.length} followers</span>
            <span className="badge">{following.length} following</span>
          </div>
        </section>

        <section className="card">
          <h3>Posts</h3>
          {posts.map((post) => (
            <article key={post.id} className="post">
              <div className="avatar" />
              <div>
                <div className="post-author">
                  {post.author.display_name}
                  <span className="post-meta">@{post.author.handle}</span>
                  <span className="badge">{post.topic}</span>
                </div>
                <div className="post-submeta">
                  <span
                    className={`follow-pill ${
                      post.author.id === 1 ? "self" : viewerFollowingIds.has(post.author.id) ? "on" : "off"
                    }`}
                  >
                    {post.author.id === 1
                      ? "You"
                      : viewerFollowingIds.has(post.author.id)
                      ? "Following"
                      : "Not following"}
                  </span>
                  <span className="post-meta">{formatPostDate(post.created_at)}</span>
                </div>
                <p className="post-content">{post.content}</p>
                <div className="post-actions">
                  <button
                    className="post-action"
                    onClick={() =>
                      likePost(post.id)
                        .then(() => fetchUserPosts(userId).then(setPosts))
                        .catch(() => null)
                    }
                  >
                    Like {post.like_count}
                  </button>
                  <span>Replies {post.reply_count}</span>
                  <span>Reposts {post.repost_count}</span>
                </div>
              </div>
            </article>
          ))}
        </section>
      </main>

      <aside className="sidebar right-rail">
        <div className="card">
          <h3>Connections</h3>
          <p className="post-meta">See who @{user?.handle} follows vs discovers</p>
          <div className="segmented">
            <button
              type="button"
              className={connectionView === "following" ? "active" : ""}
              onClick={() => setConnectionView("following")}
            >
              Following
            </button>
            <button
              type="button"
              className={connectionView === "not_following" ? "active" : ""}
              onClick={() => setConnectionView("not_following")}
            >
              Not Following
            </button>
          </div>
          {connectionList.length ? (
            connectionList.map((person) => (
              <a key={person.id} className="user-item" href={`/profile/${person.id}`}>
                <strong>{person.display_name}</strong>
                <div className="post-meta">
                  @{person.handle} · {person.persona_type}
                </div>
              </a>
            ))
          ) : (
            <p className="post-meta">
              {connectionView === "following"
                ? "Not following anyone yet."
                : "Everyone here is already followed."}
            </p>
          )}
        </div>
      </aside>
    </div>
  );
}
