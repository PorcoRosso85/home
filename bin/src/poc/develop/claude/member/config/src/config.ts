#!/usr/bin/env -S deno run --allow-all

/**
 * Claude Config Generation Script
 * 
 * 標準入力: ConfigInput (JSON)
 * 標準出力: ConfigOutput (JSON)
 * 副作用: settings.json生成（必要な場合）
 */

import type { ConfigInput, ConfigOutput, ConfigPreset, SdkOptions, SettingsJson } from "./types.ts";

// プリセット定義
const PRESETS: Record<string, ConfigPreset> = {
  readonly: {
    name: "readonly",
    sdkOptions: {
      allowedTools: ["Read", "Glob", "Grep", "LS"],
      permissionMode: "default"
    },
    settings: {}
  },
  development: {
    name: "development",
    sdkOptions: {
      allowedTools: ["*"],
      permissionMode: "acceptEdits",
      verbose: true
    },
    settings: {
      env: {
        ENVIRONMENT: "development",
        DEBUG: "1"
      }
    }
  },
  production: {
    name: "production",
    sdkOptions: {
      allowedTools: ["Read", "Glob", "Grep"],
      disallowedTools: ["Bash", "Write", "Edit"],
      permissionMode: "default"
    },
    settings: {
      permissions: {
        deny: ["Bash(rm:*)", "Bash(dd:*)", "Write(/etc/**)"],
        additionalDirectories: []
      },
      env: {
        ENVIRONMENT: "production",
        DISABLE_COST_WARNINGS: "0"
      }
    }
  }
};

async function generateSettingsJson(settings: SettingsJson, workdir: string): Promise<string | undefined> {
  if (Object.keys(settings).length === 0) {
    return undefined;
  }

  const settingsDir = `${workdir}/.claude`;
  await Deno.mkdir(settingsDir, { recursive: true });
  
  const settingsPath = `${settingsDir}/settings.json`;
  await Deno.writeTextFile(settingsPath, JSON.stringify(settings, null, 2));
  
  return settingsPath;
}

async function main() {
  try {
    // 標準入力から読み取り
    const input = await Deno.readTextFile("/dev/stdin");
    const config: ConfigInput = JSON.parse(input);

    // デフォルト値
    const mode = config.mode || "readonly";
    const workdir = config.workdir || Deno.cwd();
    
    // プリセット取得
    const preset = PRESETS[mode];
    if (!preset) {
      console.error(JSON.stringify({
        error: `Unknown mode: ${mode}`,
        code: "PRESET_NOT_FOUND"
      }));
      Deno.exit(1);
    }

    // 環境変数のマージ
    const mergedSettings: SettingsJson = {
      ...preset.settings,
      env: {
        ...preset.settings.env,
        ...config.env
      }
    };

    // settings.json生成
    const settingsPath = await generateSettingsJson(mergedSettings, workdir);

    // 出力生成
    const output: ConfigOutput = {
      prompt: config.prompt,
      workdir,
      claudeId: `${mode}-${Date.now()}`,
      sdkOptions: preset.sdkOptions,
      settingsPath
    };

    // 標準出力へ
    console.log(JSON.stringify(output));

  } catch (error) {
    console.error(JSON.stringify({
      error: String(error),
      code: "IO_ERROR"
    }));
    Deno.exit(1);
  }
}

// スクリプトとして実行された場合
if (import.meta.main) {
  await main();
}

// テスト用エクスポート
export { PRESETS, generateSettingsJson };