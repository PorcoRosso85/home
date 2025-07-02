// Type definitions for claude SDK

export type SessionHistory = Array<[string, string]>;
export type Session = { h: SessionHistory };

// Stream entry with metadata
export type StreamEntry = {
  claude_id: string;
  timestamp: string;
  data: unknown;
};

export type StreamEntryWithWorktree = {
  worktree_uri: string;
  process_id: number;
  timestamp: string;
  data: unknown;
};

