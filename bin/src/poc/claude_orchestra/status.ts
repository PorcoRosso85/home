#!/usr/bin/env -S deno run --allow-env --allow-read
import { join } from "@std/path";

async function status(worktree: string) {
  try {
    const worktreeRoot = join(Deno.env.get("HOME")!, "worktree-practice");
    const sessionPath = join(worktreeRoot, `work-${worktree}`, ".claude_session", "stream.jsonl");
    const content = await Deno.readTextFile(sessionPath);
    const lines = content.trim().split("\n");
    
    console.log(`\n=== ${worktree} の最新状態 ===`);
    console.log(lines.slice(-10).join("\n"));
  } catch (err) {
    console.error(`${worktree} のセッションが見つかりません`);
  }
}

// CLI実行
if (import.meta.main) {
  const worktree = Deno.args[0];
  if (!worktree) {
    console.error("Usage: deno task status <worktree>");
    Deno.exit(1);
  }
  await status(worktree);
}