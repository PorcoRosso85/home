/**
 * Claude Orchestra Module
 * 
 * 複数のClaude POCを統合したパイプライン実行
 * 
 * 使用例:
 * ```typescript
 * import { runPipeline } from "./mod.ts";
 * 
 * const result = await runPipeline({
 *   prompt: "Review this code",
 *   mode: "readonly",
 *   workdir: "/tmp/project"
 * });
 * 
 * if (result.sdkResult?.success) {
 *   console.log("Success!");
 * }
 * ```
 */

export { runConfig, runSdk, runPipeline } from "./helpers.ts";
export type {
  ConfigOutput,
  SdkInput,
  TestScenario,
  OrchestraError
} from "./types.ts";