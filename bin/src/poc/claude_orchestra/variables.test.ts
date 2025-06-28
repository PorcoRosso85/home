import { assertEquals } from "https://deno.land/std@0.220.0/assert/mod.ts";
import { getConfig, getWorktreePath, getSessionPath } from "./variables.ts";

Deno.test("getConfig: デフォルト値が正しく設定される", () => {
  const config = getConfig();
  
  assertEquals(config.worktreeRoot, Deno.cwd());
  assertEquals(config.sessionDirName, "");
  assertEquals(config.claudeSdkPath, "../claude_sdk/claude.ts");
});

Deno.test("getConfig: 環境変数が優先される", async (t) => {
  // 環境変数を設定
  Deno.env.set("WORKTREE_ROOT", "/custom/root");
  Deno.env.set("SESSION_DIR_NAME", ".logs");
  Deno.env.set("CLAUDE_SDK_PATH", "/custom/claude.ts");
  
  const config = getConfig();
  
  assertEquals(config.worktreeRoot, "/custom/root");
  assertEquals(config.sessionDirName, ".logs");
  assertEquals(config.claudeSdkPath, "/custom/claude.ts");
  
  // クリーンアップ
  Deno.env.delete("WORKTREE_ROOT");
  Deno.env.delete("SESSION_DIR_NAME");
  Deno.env.delete("CLAUDE_SDK_PATH");
});

Deno.test("getWorktreePath: パスが正しく結合される", () => {
  const config = {
    worktreeRoot: "/home/user/project",
    sessionDirName: "",
    claudeSdkPath: ""
  };
  
  const path = getWorktreePath(config, "feature/auth");
  assertEquals(path, "/home/user/project/feature/auth");
});

Deno.test("getSessionPath: sessionDirNameが空の場合はworktreePath", () => {
  const config = {
    worktreeRoot: "/home/user/project",
    sessionDirName: "",
    claudeSdkPath: ""
  };
  
  const path = getSessionPath(config, "feature/auth");
  assertEquals(path, "/home/user/project/feature/auth");
});

Deno.test("getSessionPath: sessionDirNameがある場合は結合される", () => {
  const config = {
    worktreeRoot: "/home/user/project",
    sessionDirName: ".logs",
    claudeSdkPath: ""
  };
  
  const path = getSessionPath(config, "feature/auth");
  assertEquals(path, "/home/user/project/feature/auth/.logs");
});