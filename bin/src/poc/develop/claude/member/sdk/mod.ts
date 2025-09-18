/**
 * Claude SDK for Deno - Minimal Claude CLI wrapper with automatic session continuation
 * 
 * ## Usage example:
 * 
 * ```typescript
 * import { main } from "https://deno.land/x/claude_sdk/mod.ts";
 * 
 * // Direct command line usage
 * await main(["--claude-id", "task-123", "--uri", ".claude", "--print", "Hello Claude!"]);
 * 
 * // Or use individual functions
 * import { parseArgs, loadSession, saveSession, buildPrompt } from "https://deno.land/x/claude_sdk/mod.ts";
 * 
 * const { claudeId, uri, prompt } = parseArgs(["--claude-id", "test", "--uri", ".claude", "--print", "Hello"]);
 * const session = await loadSession(uri);
 * const fullPrompt = buildPrompt(session.h, prompt);
 * console.log(fullPrompt);
 * 
 * // Format data to JSONL with metadata
 * const jsonl = formatToJsonl({ type: "user", message: "Hello" }, claudeId);
 * console.log(jsonl);  // Output to console
 * await appendStream(uri, jsonl);  // Persist to file
 * ```
 * 
 * ## CLI usage:
 * 
 * ```bash
 * # Run with deno task
 * deno task claude --claude-id task-123 --uri .claude --print "Hello Claude!"
 * 
 * # Or run directly
 * deno run --allow-all https://deno.land/x/claude_sdk/claude.ts --claude-id my-task --uri .claude --print "Hello"
 * ```
 * 
 * ## Features:
 * - Automatic session continuation with conversation history
 * - Maintains last 6 exchanges as context
 * - Saves conversation to `<uri>/session.json`
 * - Saves stream with metadata to `<uri>/stream.jsonl`
 * - Sets Claude's working directory to the --uri path
 * - Standard error handling with try/catch
 */

export { main } from "./claude.ts";
export { parseArgs, loadSession, saveSession, appendStream, buildPrompt, formatToJsonl } from "./core.ts";
export type {
  SessionHistory,
  Session,
  StreamEntry
} from "./types.ts";