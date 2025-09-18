/**
 * Claude Config Pipeline Module
 * 
 * 設定生成パイプラインのコンポーネント群
 * 
 * 使用例（パイプライン）:
 * ```bash
 * echo '{"prompt": "Review", "mode": "readonly"}' | ./config.ts | claude-sdk
 * ```
 * 
 * 使用例（プログラム）:
 * ```typescript
 * import { PRESETS, generateSettingsJson } from "./mod.ts";
 * 
 * const preset = PRESETS.readonly;
 * const settingsPath = await generateSettingsJson(preset.settings, "/tmp/work");
 * ```
 */

export { PRESETS, generateSettingsJson } from "./config.ts";
export type {
  ConfigInput,
  ConfigOutput,
  ConfigPreset,
  ConfigError,
  SdkOptions,
  SettingsJson
} from "./types.ts";