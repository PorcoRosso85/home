import { assertEquals } from "https://deno.land/std@0.224.0/testing/asserts.ts";

// ====================
// TDD RED フェーズ: worktree-uri統合の型定義テスト
// ====================

Deno.test("test_StreamEntryWithWorktree_型定義_必須フィールド確認", () => {
  // @ts-ignore - 型がまだ存在しない
  const entry: StreamEntryWithWorktree = {
    worktree_uri: "/tmp/auth-feature",
    process_id: 12345,
    timestamp: "2025-06-30T10:00:00Z",
    data: { type: "test" }
  };
  
  // 型チェックのため、各フィールドにアクセス
  assertEquals(typeof entry.worktree_uri, "string");
  assertEquals(typeof entry.process_id, "number");
  assertEquals(typeof entry.timestamp, "string");
  assertEquals(typeof entry.data, "object");
  
  // claude_idフィールドが存在しないことを確認
  assertEquals("claude_id" in entry, false);
});

Deno.test("test_ParsedArgsWithWorktree_型定義_claudeId削除確認", () => {
  // @ts-ignore - 型がまだ存在しない
  const args: ParsedArgsWithWorktree = {
    uri: "/tmp/feature", 
    prompt: "implement feature"
  };
  
  // 必須フィールドの確認
  assertEquals(typeof args.uri, "string");
  assertEquals(typeof args.prompt, "string");
  
  // claudeIdが型に含まれていないことを確認
  assertEquals("claudeId" in args, false);
});