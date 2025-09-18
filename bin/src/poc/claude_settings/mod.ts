/**
 * Claude Settings Dynamic Permission Control POC
 * 
 * 概要:
 * Claude Codeのsettings.jsonを動的に書き換えることで、
 * 実行時の権限制御を実現するPOC
 * 
 * 使用例:
 * ```typescript
 * // 権限制御設定
 * const settings = {
 *   allowedTools: ["Read", "Glob"],  // 読み取り専用
 *   hooks: {
 *     PreToolUse: [{
 *       matcher: ".*",
 *       hooks: [{
 *         type: "command",
 *         command: "echo 'Tool used' >> audit.log"
 *       }]
 *     }]
 *   }
 * };
 * 
 * // 設定を適用してClaude実行
 * await createSettings("/tmp/work", settings);
 * const cmd = await getClaudeCommand();
 * // ... Claude実行
 * ```
 */

export { getClaudeCommand, createSettings } from "./test_utils.ts";

// テスト実行方法:
// deno test --allow-all
// nix run .#test-red  (TDD Red phase)