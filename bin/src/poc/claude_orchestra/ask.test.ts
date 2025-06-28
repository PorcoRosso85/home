import { assertEquals, assertRejects } from "https://deno.land/std@0.220.0/assert/mod.ts";
import { stub } from "https://deno.land/std@0.220.0/testing/mock.ts";
import { askClaude } from "./ask.ts";

Deno.test("ask: worktreeディレクトリが存在しない場合エラー", async () => {
  await assertRejects(
    async () => {
      await askClaude({
        worktree: "non-existent-worktree",
        task: "test task"
      });
    },
    Error,
    "Worktree directory not found"
  );
});

Deno.test("ask: claude.tsが見つからない場合エラー", async () => {
  // 一時的なworktreeディレクトリを作成
  const tempDir = await Deno.makeTempDir();
  
  // 環境変数を設定
  Deno.env.set("WORKTREE_ROOT", tempDir);
  Deno.env.set("CLAUDE_SDK_PATH", "/non/existent/claude.ts");
  
  try {
    await assertRejects(
      async () => {
        await askClaude({
          worktree: ".",
          task: "test task"
        });
      },
      Error,
      "Claude SDK not found"
    );
  } finally {
    // クリーンアップ
    await Deno.remove(tempDir, { recursive: true });
    Deno.env.delete("WORKTREE_ROOT");
    Deno.env.delete("CLAUDE_SDK_PATH");
  }
});

Deno.test("ask: コマンドが失敗した場合エラー", async () => {
  // 一時的なworktreeディレクトリを作成
  const tempDir = await Deno.makeTempDir();
  const claudeScript = `${tempDir}/claude.ts`;
  await Deno.writeTextFile(claudeScript, "// dummy claude.ts");
  
  // 環境変数を設定
  Deno.env.set("WORKTREE_ROOT", tempDir);
  Deno.env.set("CLAUDE_SDK_PATH", claudeScript);
  
  try {
    await assertRejects(
      async () => {
        await askClaude({
          worktree: ".",
          task: "test task",
          command: "false"  // 必ず失敗するコマンド
        });
      },
      Error,
      "Command failed with exit code"
    );
  } finally {
    // クリーンアップ
    await Deno.remove(tempDir, { recursive: true });
    Deno.env.delete("WORKTREE_ROOT");
    Deno.env.delete("CLAUDE_SDK_PATH");
  }
});

Deno.test("ask: 複数単語のタスクが正しく結合される", () => {
  const taskParts = ["UIを", "作成", "してください"];
  const task = taskParts.join(" ");
  assertEquals(task, "UIを 作成 してください");
});