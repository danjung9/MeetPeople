"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchGraph } from "../lib/api";

export default function GraphClient() {
  const [graph, setGraph] = useState<{
    nodes: { id: number; handle: string; persona_type: string }[];
    edges: { source: number; target: number }[];
  }>({ nodes: [], edges: [] });

  useEffect(() => {
    fetchGraph().then(setGraph).catch(() => null);
  }, []);

  const adjacency = useMemo(() => {
    const map = new Map<number, number[]>();
    graph.nodes.forEach((node) => map.set(node.id, []));
    graph.edges.forEach((edge) => {
      const list = map.get(edge.source) || [];
      list.push(edge.target);
      map.set(edge.source, list);
    });
    return map;
  }, [graph]);

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
          <h2>Follow Graph</h2>
          {graph.nodes.map((node) => {
            const followees = adjacency.get(node.id) || [];
            return (
              <div key={node.id} className="trend-item">
                <strong>@{node.handle}</strong>
                <div className="post-meta">{node.persona_type}</div>
                <div className="post-meta">
                  Follows: {followees.map((id) => graph.nodes.find((n) => n.id === id)?.handle).join(", ")}
                </div>
              </div>
            );
          })}
        </section>
      </main>
    </div>
  );
}
