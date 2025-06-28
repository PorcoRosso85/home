import { assertEquals, assertRejects } from "https://deno.land/std@0.220.0/assert/mod.ts";
import { getStatus, formatStatus } from "./status.ts";

Deno.test("status: stream.jsonlが存在しない場合エラーメッセージ", async () => {
  // 一時的なworktreeディレクトリを作成（ファイルなし）
  const tempDir = await Deno.makeTempDir();
  
  Deno.env.set("WORKTREE_ROOT", tempDir);
  
  try {
    await assertRejects(
      async () => {
        await getStatus({ worktree: "." });
      },
      Error,
      "Session file not found"
    );
  } finally {
    await Deno.remove(tempDir, { recursive: true });
    Deno.env.delete("WORKTREE_ROOT");
  }
});

Deno.test("status: 空のstream.jsonlの場合でも動作", async () => {
  // 一時的なworktreeディレクトリとファイルを作成
  const tempDir = await Deno.makeTempDir();
  await Deno.writeTextFile(`${tempDir}/stream.jsonl`, "");
  
  Deno.env.set("WORKTREE_ROOT", tempDir);
  
  try {
    const result = await getStatus({ worktree: "." });
    assertEquals(result, "");
  } finally {
    await Deno.remove(tempDir, { recursive: true });
    Deno.env.delete("WORKTREE_ROOT");
  }
});

Deno.test("status: 10行以下の場合は全行表示", async () => {
  // 一時的なworktreeディレクトリとファイルを作成
  const tempDir = await Deno.makeTempDir();
  const content = "line1\nline2\nline3";
  await Deno.writeTextFile(`${tempDir}/stream.jsonl`, content);
  
  Deno.env.set("WORKTREE_ROOT", tempDir);
  
  try {
    const result = await getStatus({ worktree: "." });
    assertEquals(result, "line1\nline2\nline3");
  } finally {
    await Deno.remove(tempDir, { recursive: true });
    Deno.env.delete("WORKTREE_ROOT");
  }
});

Deno.test("status: 10行以上の場合は最後の10行のみ", async () => {
  // 一時的なworktreeディレクトリとファイルを作成
  const tempDir = await Deno.makeTempDir();
  const lines = Array.from({length: 20}, (_, i) => `line${i + 1}`);
  await Deno.writeTextFile(`${tempDir}/stream.jsonl`, lines.join("\n"));
  
  Deno.env.set("WORKTREE_ROOT", tempDir);
  
  try {
    const result = await getStatus({ worktree: "." });
    const resultLines = result.split("\n");
    assertEquals(resultLines.length, 10);
    assertEquals(resultLines[0], "line11");
    assertEquals(resultLines[9], "line20");
  } finally {
    await Deno.remove(tempDir, { recursive: true });
    Deno.env.delete("WORKTREE_ROOT");
  }
});

Deno.test("status: worktreeディレクトリが存在しない場合", async () => {
  await assertRejects(
    async () => {
      await getStatus({ worktree: "non-existent" });
    },
    Error,
    "Worktree directory not found"
  );
});

Deno.test("formatStatus: 正しくフォーマットされる", () => {
  const result = formatStatus("feature/auth", "test content");
  assertEquals(result, "\n=== feature/auth の最新状態 ===\ntest content");
});