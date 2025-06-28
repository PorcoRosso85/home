#!/usr/bin/env -S deno run --allow-env --allow-read --allow-run
import { getConfig, getSessionPath } from "./variables.ts";
import { exists } from "https://deno.land/std@0.220.0/fs/mod.ts";

export interface AskOptions {
  worktree: string;
  task: string;
  command?: string;  // テスト用にコマンドを差し替え可能
}

// テスト可能な関数として分離
export async function askClaude(options: AskOptions): Promise<void> {
  const config = getConfig();
  const sessionDir = getSessionPath(config, options.worktree);
  
  // worktreeディレクトリの存在確認
  const worktreeExists = await exists(sessionDir, { isDirectory: true });
  if (!worktreeExists) {
    throw new Error(`Worktree directory not found: ${sessionDir}`);
  }
  
  // claude.tsの存在確認
  const claudePath = config.claudeSdkPath;
  const claudeExists = await exists(claudePath, { isFile: true });
  if (!claudeExists) {
    throw new Error(`Claude SDK not found: ${claudePath}`);
  }
  
  const command = options.command || "tsx";
  const proc = new Deno.Command(command, {
    args: [
      claudePath,
      "--uri", sessionDir,
      "--print", options.task
    ],
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit"
  });
  
  const status = await proc.output();
  if (!status.success) {
    throw new Error(`Command failed with exit code ${status.code}`);
  }
}

// CLI実行
if (import.meta.main) {
  const [worktree, ...taskParts] = Deno.args;
  if (!worktree) {
    console.error("Usage: deno task ask <worktree> <task>");
    console.error("Example: deno task ask feature/auth 'Implement authentication'");
    Deno.exit(1);
  }
  
  try {
    await askClaude({
      worktree,
      task: taskParts.join(" ")
    });
  } catch (error) {
    console.error(`Error: ${error.message}`);
    Deno.exit(1);
  }
}