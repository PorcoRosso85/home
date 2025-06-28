#!/usr/bin/env -S deno run --allow-env --allow-read --allow-run
import { join } from "@std/path";

// CLIとして直接実行可能
async function ask(worktree: string, task: string) {
  // worktree-practiceディレクトリのパス
  const worktreeRoot = join(Deno.env.get("HOME")!, "worktree-practice");
  const sessionDir = join(worktreeRoot, `work-${worktree}`, ".claude_session");
  
  const proc = new Deno.Command("tsx", {
    args: [
      "../claude_sdk/claude.ts",
      "--uri", sessionDir,
      "--print", task
    ],
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit"
  });
  
  const status = await proc.output();
  if (!status.success) {
    Deno.exit(1);
  }
}

// CLI実行
if (import.meta.main) {
  const [worktree, ...taskParts] = Deno.args;
  if (!worktree) {
    console.error("Usage: deno task ask <worktree> <task>");
    Deno.exit(1);
  }
  await ask(worktree, taskParts.join(" "));
}