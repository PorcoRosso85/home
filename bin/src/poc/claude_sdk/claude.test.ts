import { assertEquals, assertThrows } from "https://deno.land/std@0.224.0/testing/asserts.ts";
import { parseArgs, buildPrompt, loadSession, saveSession, appendStream } from "./core.ts";

// parseArgs tests
Deno.test("test_parseArgs_valid_returnsUriAndPrompt", () => {
  const result = parseArgs(["--uri", "test", "--print", "hello", "world"]);
  assertEquals(result.uri, "test");
  assertEquals(result.prompt, "hello world");
});

Deno.test("test_parseArgs_missingUri_throwsError", () => {
  assertThrows(
    () => parseArgs(["--print", "test"]),
    Error,
    "Usage:"
  );
});

Deno.test("test_parseArgs_missingPrint_throwsError", () => {
  assertThrows(
    () => parseArgs(["--uri", "test"]),
    Error,
    "Usage:"
  );
});

Deno.test("test_parseArgs_emptyValues_throwsError", () => {
  assertThrows(
    () => parseArgs(["--uri", "", "--print", ""]),
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
Deno.test("test_appendStream_withMetadata_addsIdAndTimestamp", async () => {
  const tempDir = await Deno.makeTempDir();
  const testData = { type: "test", content: "hello" };
  
  await appendStream(tempDir, JSON.stringify(testData), true);
  
  const content = await Deno.readTextFile(`${tempDir}/stream.jsonl`);
  const parsed = JSON.parse(content.trim());
  
  assertEquals(typeof parsed.id, "string");
  assertEquals(parsed.id.length, 36); // UUID length
  assertEquals(typeof parsed.timestamp, "string");
  assertEquals(parsed.timestamp.includes("T"), true); // ISO format
  assertEquals(parsed.data, testData);
  
  await Deno.remove(tempDir, { recursive: true });
});

Deno.test("test_appendStream_withoutMetadata_appendsRawLine", async () => {
  const tempDir = await Deno.makeTempDir();
  const testLine = "raw test line";
  
  await appendStream(tempDir, testLine, false);
  
  const content = await Deno.readTextFile(`${tempDir}/stream.jsonl`);
  assertEquals(content.trim(), testLine);
  
  await Deno.remove(tempDir, { recursive: true });
});

Deno.test("test_appendStream_invalidJson_appendsAsIs", async () => {
  const tempDir = await Deno.makeTempDir();
  const invalidJson = "not valid json {";
  
  await appendStream(tempDir, invalidJson, true);
  
  const content = await Deno.readTextFile(`${tempDir}/stream.jsonl`);
  assertEquals(content.trim(), invalidJson);
  
  await Deno.remove(tempDir, { recursive: true });
});