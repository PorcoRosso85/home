/**
 * Claude Orchestra Types - POC間のインターフェース定義
 */

// claude_config の出力
export type ConfigOutput = {
  prompt: string;
  workdir: string;
  claudeId: string;
  sdkOptions: {
    allowedTools?: string[];
    disallowedTools?: string[];
    permissionMode?: string;
  };
  settingsPath?: string;
};

// claude_sdk への入力
export type SdkInput = {
  claudeId: string;
  uri: string;
  prompt: string;
  allowWrite?: boolean;
};

// 統合テストのシナリオ
export type TestScenario = {
  name: string;
  mode: "readonly" | "development" | "production";
  prompt: string;
  expectedBehavior: {
    shouldAllowWrite: boolean;
    shouldAllowBash: boolean;
    shouldBlockDangerousCommands: boolean;
  };
};

// エラー型
export type OrchestraError = {
  stage: "config" | "sdk" | "validation";
  error: string;
  code: string;
};