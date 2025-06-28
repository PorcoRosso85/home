import { assertEquals, assertThrows } from "https://deno.land/std@0.224.0/testing/asserts.ts";
import { parseArgs, buildPrompt, loadSession, saveSession, appendStream, formatToJsonl } from "./core.ts";

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

