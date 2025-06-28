import { join } from "@std/path";

export interface Config {
  worktreeRoot: string;
  sessionDirName: string;
  claudeSdkPath: string;
}

export function getConfig(): Config {
  const home = Deno.env.get("HOME") || "/home/user";
  
  return {
    worktreeRoot: Deno.env.get("WORKTREE_ROOT") || Deno.cwd(),
    sessionDirName: Deno.env.get("SESSION_DIR_NAME") || "",  // worktreeルートに直接保存
    claudeSdkPath: Deno.env.get("CLAUDE_SDK_PATH") || "../claude_sdk/claude.ts"
  };
}

export function getWorktreePath(config: Config, worktree: string): string {
  return join(config.worktreeRoot, worktree);
}

export function getSessionPath(config: Config, worktree: string): string {
  const worktreePath = getWorktreePath(config, worktree);
  return config.sessionDirName ? join(worktreePath, config.sessionDirName) : worktreePath;
}