import { join } from "https://deno.land/std@0.224.0/path/mod.ts";
import type { SessionHistory, Session, StreamEntry } from "./types.ts";

// Parse arguments
export function parseArgs(args: string[]): { uri: string; prompt: string } {
  const uriIndex = args.indexOf("--uri");
  const printIndex = args.indexOf("--print");
  
  if (uriIndex === -1 || printIndex === -1) {
    throw new Error("Usage: deno run claude.ts --uri <directory> --print <prompt>");
  }
  
  const uri = args[uriIndex + 1];
  const prompt = args.slice(printIndex + 1).join(" ");
  
  if (!uri || !prompt) {
    throw new Error("Both --uri and --print are required");
  }
  
  return { uri, prompt };
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

export async function appendStream(dir: string, line: string, addMetadata = true): Promise<void> {
  const encoder = new TextEncoder();
  let outputLine = line;
  
  if (addMetadata) {
    try {
      const entry: StreamEntry = {
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        data: JSON.parse(line)
      };
      outputLine = JSON.stringify(entry);
    } catch {
      // If line is not valid JSON, append as is
    }
  }
  
  const data = encoder.encode(outputLine + "\n");
  
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