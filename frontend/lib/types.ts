export type User = {
  id: number;
  handle: string;
  display_name: string;
  bio: string;
  avatar_url: string;
  persona_type: string;
};

export type Post = {
  id: number;
  author: User;
  content: string;
  topic: string;
  created_at: string;
  like_count: number;
  reply_count: number;
  repost_count: number;
  quote_count: number;
  is_reply: boolean;
  reply_to_id: number | null;
};

export type Explanation = {
  score: number;
  components: Record<string, number>;
  notes: string[];
  stage_log: string[];
  action_probs: Record<string, number>;
};

export type FeedItem = {
  post: Post;
  explanation: Explanation;
};

export type FeedResponse = {
  items: FeedItem[];
  generated_at: string;
};

export type Trend = {
  topic: string;
  score: number;
};

export type Notification = {
  id: number;
  title: string;
  body: string;
  created_at: string;
  is_read: boolean;
};

export type Graph = {
  nodes: { id: number; handle: string; persona_type: string }[];
  edges: { source: number; target: number }[];
};
