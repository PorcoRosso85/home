import { assertEquals, assertThrows, assertExists, assertStringIncludes } from "https://deno.land/std@0.224.0/testing/asserts.ts";
import { parseArgs, buildPrompt, loadSession, saveSession, appendStream, formatToJsonl } from "./core.ts";
// @ts-ignore - main関数をテスト用にインポート
import { main } from "./claude.ts";

// parseArgs tests
Deno.test("test_parseArgs_valid_returnsAllParams", () => {
  const result = parseArgs(["--claude-id", "test-id", "--uri", "test", "--print", "hello", "world"]);
  assertEquals(result.claudeId, "test-id");
  assertEquals(result.uri, "test");
  assertEquals(result.prompt, "hello world");
});

Deno.test("test_parseArgs_missingClaudeId_throwsError", () => {
  assertThrows(
    () => parseArgs(["--uri", "test", "--print", "hello"]),
    Error,
    "--claude-id is required"
  );
});

Deno.test("test_parseArgs_missingUri_throwsError", () => {
  assertThrows(
    () => parseArgs(["--claude-id", "test-id", "--print", "test"]),
    Error,
    "Usage:"
  );
});

Deno.test("test_parseArgs_missingPrint_throwsError", () => {
  assertThrows(
    () => parseArgs(["--claude-id", "test-id", "--uri", "test"]),
    Error,
    "Usage:"
  );
});

Deno.test("test_parseArgs_emptyClaudeId_throwsError", () => {
  assertThrows(
    () => parseArgs(["--claude-id", "", "--uri", "test", "--print", "hello"]),
    Error,
    "--claude-id cannot be empty"
  );
});

Deno.test("test_parseArgs_emptyValues_throwsError", () => {
  assertThrows(
    () => parseArgs(["--claude-id", "test-id", "--uri", "", "--print", ""]),
    Error,
    "required"
  );
});

// buildPrompt tests
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

Deno.test("test_buildPrompt_longHistory_limitsToSix", () => {
  const history: Array<[string, string]> = Array.from(
    { length: 10 },
    (_, i) => ["user", `msg${i}`]
  );
  const result = buildPrompt(history, "new");
  assertEquals(result.includes("msg9"), true);
  assertEquals(result.includes("msg3"), false);
});

// Session persistence tests
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

// appendStream tests
Deno.test("test_appendStream_writesLineToFile", async () => {
  const tempDir = await Deno.makeTempDir();
  const testLine = "test line";
  
  await appendStream(tempDir, testLine);
  
  const content = await Deno.readTextFile(`${tempDir}/stream.jsonl`);
  assertEquals(content.trim(), testLine);
  
  await Deno.remove(tempDir, { recursive: true });
});

// formatToJsonl tests
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

Deno.test("test_formatToJsonl_stringWithoutClaudeId_returnsString", () => {
  const testString = "raw string";
  const result = formatToJsonl(testString);
  assertEquals(result, testString);
});

// 統合テスト：session.jsonなしでは会話継続できない
Deno.test("test_sessionJson必要性_なし_文脈が失われる", async () => {
  const tempDir = await Deno.makeTempDir();
  const testUri = tempDir;
  
  try {
    // 1回目：数字を記憶させる
    const cmd1 = new Deno.Command("claude", {
      args: ["--print", "123という数字を覚えてください", "--continue", "--output-format", "stream-json", "--verbose"],
      cwd: testUri,
      env: { ...Deno.env.toObject(), CLAUDE_NON_INTERACTIVE: "1" },
      stdout: "piped",
      stderr: "piped"
    });
    
    const result1 = await cmd1.output();
    const output1 = new TextDecoder().decode(result1.stdout);
    assertStringIncludes(output1, "123");  // 数字を認識したはず
    
    // 2回目：前の数字を聞く（session.jsonなし）
    const cmd2 = new Deno.Command("claude", {
      args: ["--print", "覚えた数字は何でしたか？", "--continue", "--output-format", "stream-json", "--verbose"],
      cwd: testUri,
      env: { ...Deno.env.toObject(), CLAUDE_NON_INTERACTIVE: "1" },
      stdout: "piped",
      stderr: "piped"
    });
    
    const result2 = await cmd2.output();
    const output2 = new TextDecoder().decode(result2.stdout);
    
    // session.jsonがないので、数字を覚えていないはず
    // しかし、Claude CLIの--continueが効いて覚えている可能性もある
    console.log("Output without session.json:", output2.includes("123"));
    
    // この時点でsession_idが異なることを確認
    const sessionId1 = output1.match(/"session_id":"([^"]+)"/)?.[1];
    const sessionId2 = output2.match(/"session_id":"([^"]+)"/)?.[1];
    
    // 重要：session_idが毎回変わる！
    assertExists(sessionId1);
    assertExists(sessionId2);
    assertEquals(sessionId1 === sessionId2, false, "session_idは毎回異なるはず");
    
  } finally {
    await Deno.remove(tempDir, { recursive: true });
  }
});

// buildPromptの重要性：明示的な文脈構築
Deno.test("test_buildPrompt_文脈構築_session履歴を含む", () => {
  const history: Array<[string, string]> = [
    ["user", "123を覚えて"],
    ["assistant", "123を覚えました"],
  ];
  
  const prompt = buildPrompt(history, "覚えた数字は？");
  
  // buildPromptは過去の会話を明示的に含める
  assertStringIncludes(prompt, "123を覚えて");
  assertStringIncludes(prompt, "123を覚えました");
  assertStringIncludes(prompt, "覚えた数字は？");
  
  // これにより、session_idが変わっても文脈が保持される
});

// claude_sdk vs 直接CLIの比較テスト（このテストは失敗するはず）
Deno.test("test_比較_SDK対CLI_文脈保持の違い", async () => {
  const tempDir1 = await Deno.makeTempDir();
  const tempDir2 = await Deno.makeTempDir();
  
  try {
    // ケース1: claude_sdk使用（session.jsonあり）
    // 期待：文脈が保持される（ただし現在は未実装なので失敗）
    await main(["--claude-id", "test", "--uri", tempDir1, "--print", "私の名前は太郎です"]);
    await main(["--claude-id", "test", "--uri", tempDir1, "--print", "私の名前は何でしたか？"]);
    
    const sdkStream = await Deno.readTextFile(`${tempDir1}/stream.jsonl`);
    const sdkHasContext = sdkStream.includes("太郎");
    
    // ケース2: CLI直接使用（session.jsonなし）
    const cli1 = new Deno.Command("claude", {
      args: ["--print", "私の名前は花子です", "--continue"],
      cwd: tempDir2,
      stdout: "piped"
    });
    await cli1.output();
    
    const cli2 = new Deno.Command("claude", {
      args: ["--print", "私の名前は何でしたか？", "--continue"],
      cwd: tempDir2,
      stdout: "piped"
    });
    const result2 = await cli2.output();
    const cliOutput = new TextDecoder().decode(result2.stdout);
    const cliHasContext = cliOutput.includes("花子");
    
    // 期待：SDKは文脈を保持、CLIは保持しない（実際は逆かも）
    console.log("SDK has context:", sdkHasContext);
    console.log("CLI has context:", cliHasContext);
    
    // このアサーションは現在の実装では失敗するはず
    assertEquals(sdkHasContext, true, "SDKは文脈を保持すべき");
    
  } finally {
    await Deno.remove(tempDir1, { recursive: true });
    await Deno.remove(tempDir2, { recursive: true });
  }
});

