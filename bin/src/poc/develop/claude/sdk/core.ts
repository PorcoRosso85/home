import { join } from "https://deno.land/std@0.224.0/path/mod.ts";
import type { SessionHistory, Session, StreamEntry, StreamEntryWithWorktree } from "./types.ts";

// Parse arguments
export function parseArgs(args: string[]): { claudeId: string; uri: string; prompt: string; allowWrite?: boolean } {
  const claudeIdIndex = args.indexOf("--claude-id");
  const uriIndex = args.indexOf("--uri");
  const printIndex = args.indexOf("--print");
  const allowWriteIndex = args.indexOf("--allow-write");
  
  if (claudeIdIndex === -1) {
    throw new Error("--claude-id is required");
  }
  
  if (uriIndex === -1 || printIndex === -1) {
    throw new Error("Usage: deno run claude.ts --claude-id <id> --uri <directory> --print <prompt>");
  }
  
  const claudeId = args[claudeIdIndex + 1];
  const uri = args[uriIndex + 1];
  const prompt = args.slice(printIndex + 1).join(" ");
  const allowWrite = allowWriteIndex !== -1;
  
  if (!claudeId) {
    throw new Error("--claude-id cannot be empty");
  }
  
  if (!uri || !prompt) {
    throw new Error("All parameters --claude-id, --uri and --print are required");
  }
  
  return { claudeId, uri, prompt, allowWrite };
}

// Persistence layer
export async function loadSession(dir: string): Promise<Session> {
  try {
    const content = await Deno.readTextFile(join(dir, "session.json"));
    return JSON.parse(content);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      return { h: [] };
    }
    throw error;
  }
}

export async function saveSession(dir: string, session: Session): Promise<void> {
  await Deno.mkdir(dir, { recursive: true });
  await Deno.writeTextFile(
    join(dir, "session.json"), 
    JSON.stringify(session, null, 2)
  );
}

export async function appendStream(dir: string, line: string): Promise<void> {
  const encoder = new TextEncoder();
  const data = encoder.encode(line + "\n");
  
  const file = await Deno.open(join(dir, "stream.jsonl"), {
    write: true,
    append: true,
    create: true,
  });
  
  try {
    await file.write(data);
  } finally {
    file.close();
  }
}

export function buildPrompt(history: SessionHistory, prompt: string): string {
  if (history.length === 0) return prompt;
  const context = history.slice(-6).map(([r, c]) => `${r}: ${c}`).join("\n");
  return `${context}\n\nUser: ${prompt}`;
}

// JSONL formatting layer
export function formatToJsonl(data: unknown, claudeId?: string): string {
  if (!claudeId || typeof data === "string") {
    return typeof data === "string" ? data : JSON.stringify(data);
  }
  
  const entry: StreamEntry = {
    claude_id: claudeId,
    timestamp: new Date().toISOString(),
    data: data
  };
  return JSON.stringify(entry);
}

export function formatToJsonlWithWorktree(data: unknown, worktreeUri: string): string {
  return JSON.stringify({
    worktree_uri: worktreeUri,
    process_id: Deno.pid,
    timestamp: new Date().toISOString(),
    data: data
  });
}

