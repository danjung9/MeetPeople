import { FeedResponse, Notification, Trend, Post, User } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchFeed(params: Record<string, string | number>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => query.set(key, String(value)));
  const res = await fetch(`${API_URL}/feed?${query.toString()}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to fetch feed");
  }
  return (await res.json()) as FeedResponse;
}

export async function fetchTrends() {
  const res = await fetch(`${API_URL}/trends`, { cache: "no-store" });
  return (await res.json()) as Trend[];
}

export async function fetchNotifications(userId: number) {
  const res = await fetch(`${API_URL}/notifications?user_id=${userId}`, { cache: "no-store" });
  return (await res.json()) as Notification[];
}

export async function fetchUser(userId: number) {
  const res = await fetch(`${API_URL}/users/${userId}`, { cache: "no-store" });
  return (await res.json()) as User;
}

export async function fetchUsers() {
  const res = await fetch(`${API_URL}/users`, { cache: "no-store" });
  return (await res.json()) as User[];
}

export async function fetchUserPosts(userId: number) {
  const res = await fetch(`${API_URL}/users/${userId}/posts`, { cache: "no-store" });
  return (await res.json()) as Post[];
}

export async function fetchFollowers(userId: number) {
  const res = await fetch(`${API_URL}/users/${userId}/followers`, { cache: "no-store" });
  return (await res.json()) as User[];
}

export async function fetchFollowing(userId: number) {
  const res = await fetch(`${API_URL}/users/${userId}/following`, { cache: "no-store" });
  return (await res.json()) as User[];
}

export async function likePost(postId: number, userId = 1) {
  const res = await fetch(`${API_URL}/posts/${postId}/like?user_id=${userId}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to like post");
  }
  return (await res.json()) as { status: string; like_count: number };
}

export async function simulateStep(steps = 1) {
  await fetch(`${API_URL}/simulate/step?steps=${steps}`, { method: "POST" });
}

export async function fetchGraph() {
  const res = await fetch(`${API_URL}/graph`, { cache: "no-store" });
  return (await res.json()) as {
    nodes: { id: number; handle: string; persona_type: string }[];
    edges: { source: number; target: number }[];
  };
}
