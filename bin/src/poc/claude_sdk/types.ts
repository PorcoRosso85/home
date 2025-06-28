// Type definitions for claude SDK

export type SessionHistory = Array<[string, string]>;
export type Session = { h: SessionHistory };

// Stream entry with metadata
export type StreamEntry = {
  claude_id: string;
  timestamp: string;
  data: unknown;
};