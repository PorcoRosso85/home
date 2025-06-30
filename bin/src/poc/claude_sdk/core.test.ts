import { assertEquals, assertExists, assertRejects } from "https://deno.land/std@0.224.0/testing/asserts.ts";
import { 
  parseArgs, 
  buildPrompt, 
  loadSession, 
  saveSession, 
  appendStream, 
  formatToJsonl,
  formatToJsonlWithWorktree 
} from "./core.ts";

// ====================
// formatToJsonl tests
// ====================

Deno.test("test_formatToJsonl_withClaudeId_addsClaudeIdAndTimestamp", () => {
  const testData = { type: "test", content: "hello" };
  const claudeId = "test-claude-id";
  const result = formatToJsonl(testData, claudeId);
  const parsed = JSON.parse(result);
  
  assertEquals(parsed.claude_id, claudeId);
  assertEquals(typeof parsed.timestamp, "string");
  assertEquals(parsed.timestamp.includes("T"), true); // ISO format
  assertEquals(parsed.data, testData);
});

Deno.test("test_formatToJsonl_withoutClaudeId_returnsJsonString", () => {
  const testData = { type: "test", content: "hello" };
  const result = formatToJsonl(testData);
  assertEquals(result, JSON.stringify(testData));
});

// ====================
// TDD RED フェーズ: worktree-uri統合のテスト
// ====================

Deno.test("test_formatToJsonlWithWorktree_正常系_worktreeUriとprocessId含む", () => {
  const testData = { type: "test", content: "hello" };
  const worktreeUri = "/tmp/auth-feature";
  
  // @ts-ignore - 関数がまだ存在しない
  const result = formatToJsonlWithWorktree(testData, worktreeUri);
  const parsed = JSON.parse(result);
  
  assertEquals(parsed.worktree_uri, worktreeUri);
  assertEquals(typeof parsed.process_id, "number");
  assertEquals(parsed.process_id, Deno.pid);
});

Deno.test("test_parseArgsWithWorktree_正常系_uriのみで動作", () => {
  // @ts-ignore - 関数がまだ存在しない
  const result = parseArgsWithWorktree(["--uri", "/tmp/feature", "--print", "hello world"]);
  
  assertEquals(result.uri, "/tmp/feature");
  assertEquals(result.prompt, "hello world");
  assertEquals("claudeId" in result, false);
});

Deno.test("test_parseArgsWithWorktree_エラー系_uri未指定", () => {
  assertThrows(
    () => {
      // @ts-ignore - 関数がまだ存在しない
      parseArgsWithWorktree(["--print", "hello"]);
    },
    Error,
    "--uri is required"
  );
});

// ====================
// session.jsonの必要性を証明するテスト
// ====================

Deno.test("test_verifySessionContinuity_worktree間_独立性確認", async () => {
  const tempDir1 = await Deno.makeTempDir();
  const tempDir2 = await Deno.makeTempDir();
  
  try {
    // Worktree1で会話
    // @ts-ignore - mainWithWorktreeは未実装
    await mainWithWorktree({
      uri: tempDir1,
      prompt: "私はWorktree1のClaude、番号は111です"
    });
    
    // Worktree2で別の会話
    // @ts-ignore - mainWithWorktreeは未実装
    await mainWithWorktree({
      uri: tempDir2,
      prompt: "私はWorktree2のClaude、番号は222です"
    });
    
    // Worktree1に戻って確認
    // @ts-ignore - mainWithWorktreeは未実装
    const result1 = await mainWithWorktree({
      uri: tempDir1,
      prompt: "私の番号は何でしたか？"
    });
    
    // session.jsonがあれば「111」と答えるはず
    assertStringIncludes(result1, "111");
    
    // Worktree2も確認
    // @ts-ignore - mainWithWorktreeは未実装
    const result2 = await mainWithWorktree({
      uri: tempDir2,
      prompt: "私の番号は何でしたか？"
    });
    
    assertStringIncludes(result2, "222");
    
    // 混在していないことを確認
    assertEquals(result1.includes("222"), false);
    assertEquals(result2.includes("111"), false);
    
  } finally {
    await Deno.remove(tempDir1, { recursive: true });
    await Deno.remove(tempDir2, { recursive: true });
  }
});

// ====================
// buildPrompt tests
// ====================

Deno.test("test_buildPrompt_noHistory_returnsPrompt", () => {
  const result = buildPrompt([], "hello");
  assertEquals(result, "hello");
});

Deno.test("test_buildPrompt_withHistory_includesContext", () => {
  const history: Array<[string, string]> = [
    ["user", "hi"],
    ["assistant", "hello"]
  ];
  const result = buildPrompt(history, "bye");
  assertEquals(result.includes("user: hi"), true);
  assertEquals(result.includes("assistant: hello"), true);
  assertEquals(result.includes("User: bye"), true);
});

// ====================
// Session persistence tests
// ====================

Deno.test("test_loadSession_fileNotFound_returnsEmptySession", async () => {
  const tempDir = await Deno.makeTempDir();
  const session = await loadSession(tempDir);
  assertEquals(session, { h: [] });
  await Deno.remove(tempDir, { recursive: true });
});

Deno.test("test_saveSession_writesJsonFile", async () => {
  const tempDir = await Deno.makeTempDir();
  const testSession = { h: [["user", "test"], ["assistant", "response"]] as Array<[string, string]> };
  
  await saveSession(tempDir, testSession);
  
  const savedData = await Deno.readTextFile(`${tempDir}/session.json`);
  assertEquals(JSON.parse(savedData), testSession);
  
  await Deno.remove(tempDir, { recursive: true });
});

// ====================
// appendStream tests
// ====================

Deno.test("test_appendStream_writesLineToFile", async () => {
  const tempDir = await Deno.makeTempDir();
  const testLine = "test line";
  
  await appendStream(tempDir, testLine);
  
  const content = await Deno.readTextFile(`${tempDir}/stream.jsonl`);
  assertEquals(content.trim(), testLine);
  
  await Deno.remove(tempDir, { recursive: true });
});