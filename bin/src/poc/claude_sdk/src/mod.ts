/**
 * Claude session management module
 * 
 * Provides session continuity for Claude CLI interactions
 * 
 * @example Basic usage:
 * ```typescript
 * import { parseJson, addToHistory, buildContext } from "./mod";
 * 
 * // Parse streaming JSON
 * const result = parseJson('{"type": "assistant"}');
 * if (result.ok) {
 *   console.log(result.data);
 * }
 * 
 * // Manage session history
 * let history = [];
 * history = addToHistory(history, "user", "Hello");
 * history = addToHistory(history, "assistant", "Hi there!");
 * 
 * // Build context for continuation
 * const context = buildContext(history);
 * console.log(context); // "user: Hello\nassistant: Hi there!"
 * ```
 * 
 * @example Run interactive session:
 * ```bash
 * tsx src/claudeContinue.ts
 * ```
 */

export {
  parseJson,
  addToHistory,
  buildContext,
  extractAssistantText,
  type ParseResult,
  type SessionHistory,
} from "./sessionManager";