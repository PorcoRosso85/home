#!/usr/bin/env -S deno run --allow-env --allow-read
import { join } from "@std/path";
import { getConfig, getSessionPath } from "./variables.ts";
import { exists } from "https://deno.land/std@0.220.0/fs/mod.ts";

export interface StatusOptions {
  worktree: string;
  lines?: number;  // 表示する行数（デフォルト: 10）
}

// テスト可能な関数として分離
export async function getStatus(options: StatusOptions): Promise<string> {
  const config = getConfig();
  const sessionDir = getSessionPath(config, options.worktree);
  const sessionPath = join(sessionDir, "stream.jsonl");
  
  // ディレクトリの存在確認
  const dirExists = await exists(sessionDir, { isDirectory: true });
  if (!dirExists) {
    throw new Error(`Worktree directory not found: ${sessionDir}`);
  }
  
  // ファイルの存在確認
  const fileExists = await exists(sessionPath, { isFile: true });
  if (!fileExists) {
    throw new Error(`Session file not found: ${sessionPath}`);
  }
  
  const content = await Deno.readTextFile(sessionPath);
  const lines = content.trim().split("\n").filter(line => line.length > 0);
  const displayLines = options.lines || 10;
  
  return lines.slice(-displayLines).join("\n");
}

// 表示用のフォーマット関数
export function formatStatus(worktree: string, content: string): string {
  return `\n=== ${worktree} の最新状態 ===\n${content}`;
}

// CLI実行
if (import.meta.main) {
  const worktree = Deno.args[0];
  if (!worktree) {
    console.error("Usage: deno task status <worktree>");
    console.error("Example: deno task status feature/auth");
    Deno.exit(1);
  }
  
  try {
    const content = await getStatus({ worktree });
    console.log(formatStatus(worktree, content));
  } catch (error) {
    console.error(`Error: ${error.message}`);
    Deno.exit(1);
  }
}