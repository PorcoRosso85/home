/**
 * Session management for Claude CLI continuity
 * Follows bin/docs/CONVENTION.yaml
 */
import { test } from "node:test";
import assert from "node:assert/strict";

// Error types
type ParseError = { ok: false; error: string };

// Success types
type ParseSuccess = { ok: true; data: any };

// Result type
export type ParseResult = ParseSuccess | ParseError;

// Session types
export type SessionHistory = Array<[string, string]>;

/**
 * Parse JSON line, return result or error
 * @example
 * const result = parseJson('{"type": "test"}');
 * if (result.ok) console.log(result.data);
 */
export function parseJson(line: string): ParseResult {
  try {
    const data = JSON.parse(line);
    return { ok: true, data };
  } catch (error) {
    return { ok: false, error: String(error) };
  }
}

/**
 * Add message to history (immutable)
 * @example
 * const newHistory = addToHistory(history, "user", "hello");
 */
export function addToHistory(
  history: SessionHistory,
  role: string,
  content: string
): SessionHistory {
  return [...history, [role, content]];
}

/**
 * Build context from recent history
 * @example
 * const context = buildContext(history, 6);
 */
export function buildContext(history: SessionHistory, maxItems = 6): string {
  const recent = history.slice(-maxItems);
  return recent.map(([role, content]) => `${role}: ${content}`).join("\n");
}

/**
 * Extract text from assistant message
 * @example
 * const text = extractAssistantText(message);
 */
export function extractAssistantText(message: any): string | null {
  const content = message?.message?.content;
  if (!content || !Array.isArray(content)) return null;
  
  const texts = content
    .filter((item: any) => item.type === "text")
    .map((item: any) => item.text || "");
  
  return texts.length > 0 ? texts.join("") : null;
}

// In-source tests
test("parseJson_valid_returnsSuccess", () => {
  const result = parseJson('{"type": "test"}');
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.data.type, "test");
  }
});

test("parseJson_invalid_returnsError", () => {
  const result = parseJson("invalid json");
  assert.equal(result.ok, false);
  if (!result.ok) {
    assert.ok(result.error.includes("JSON"));
  }
});

test("addToHistory_immutable_preservesOriginal", () => {
  const h1: SessionHistory = [["user", "hello"]];
  const h2 = addToHistory(h1, "assistant", "hi");
  assert.equal(h1.length, 1);
  assert.equal(h2.length, 2);
  assert.deepEqual(h2[1], ["assistant", "hi"]);
});

test("buildContext_limit_showsRecentOnly", () => {
  const history: SessionHistory = Array.from(
    { length: 10 },
    (_, i) => ["user", i.toString()]
  );
  const context = buildContext(history, 3);
  assert.ok(context.includes("7"));
  assert.ok(context.includes("8"));
  assert.ok(context.includes("9"));
  assert.ok(!context.includes("0"));
});

test("extractAssistantText_valid_extractsText", () => {
  const message = {
    message: {
      content: [
        { type: "text", text: "Hello" },
        { type: "text", text: " world" },
      ],
    },
  };
  const text = extractAssistantText(message);
  assert.equal(text, "Hello world");
});

test("extractAssistantText_empty_returnsNull", () => {
  const message = { message: { content: [] } };
  const text = extractAssistantText(message);
  assert.equal(text, null);
});