/**
 * Claude Config Pipeline Types
 * 
 * 参考:
 * - https://docs.anthropic.com/en/docs/claude-code/settings
 * - https://docs.anthropic.com/en/docs/claude-code/hooks
 */

// 入力: パイプラインへの入力
export type ConfigInput = {
  prompt: string;
  mode?: "readonly" | "development" | "production";
  env?: Record<string, string>;
  workdir?: string;
};

// SDKに直接渡せるオプション
export type SdkOptions = {
  allowedTools?: string[];
  disallowedTools?: string[];
  permissionMode?: "default" | "acceptEdits" | "bypassPermissions";
  systemPrompt?: string;
  appendSystemPrompt?: string;
  maxTurns?: number;
  verbose?: boolean;
};

// settings.jsonに書く必要がある設定
export type SettingsJson = {
  permissions?: {
    allow?: string[];
    deny?: string[];
    additionalDirectories?: string[];
    defaultMode?: string;
  };
  env?: Record<string, string>;
  hooks?: {
    [eventName: string]: Array<{
      matcher: string;
      hooks: Array<{
        type: string;
        command: string;
      }>;
    }>;
  };
  apiKeyHelper?: string;
  cleanupPeriodDays?: number;
  includeCoAuthoredBy?: boolean;
};

// 出力: 次のパイプラインへの出力
export type ConfigOutput = {
  prompt: string;
  workdir: string;
  claudeId: string;
  sdkOptions: SdkOptions;
  settingsPath?: string;  // settings.jsonを生成した場合のパス
};

// プリセット定義
export type ConfigPreset = {
  name: string;
  sdkOptions: SdkOptions;
  settings: SettingsJson;
};

// エラー結果
export type ConfigError = {
  error: string;
  code: "INVALID_INPUT" | "PRESET_NOT_FOUND" | "IO_ERROR";
};