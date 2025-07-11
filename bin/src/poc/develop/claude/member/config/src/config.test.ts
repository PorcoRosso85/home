import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { PRESETS, generateSettingsJson } from "./config.ts";
import type { ConfigInput, ConfigOutput } from "./types.ts";

Deno.test("config_readonlyモード_正しいSDKオプション返却", () => {
  const preset = PRESETS.readonly;
  
  // SDKオプションの検証
  assertEquals(preset.sdkOptions.allowedTools, ["Read", "Glob", "Grep", "LS"]);
  assertEquals(preset.sdkOptions.permissionMode, "default");
  
  // settings.jsonが空であることを確認
  assertEquals(Object.keys(preset.settings).length, 0);
});

Deno.test("config_productionモード_セキュリティ設定含む", () => {
  const preset = PRESETS.production;
  
  // 禁止ツールの確認
  assertEquals(preset.sdkOptions.disallowedTools, ["Bash", "Write", "Edit"]);
  
  // 危険なコマンドの拒否設定
  assertExists(preset.settings.permissions?.deny);
  assertEquals(preset.settings.permissions.deny.includes("Bash(rm:*)"), true);
});

Deno.test("generateSettingsJson_設定あり_ファイル生成", async () => {
  const tempDir = await Deno.makeTempDir();
  const settings = {
    env: {
      TEST: "true"
    }
  };
  
  const path = await generateSettingsJson(settings, tempDir);
  
  assertExists(path);
  assertEquals(path, `${tempDir}/.claude/settings.json`);
  
  // ファイルの中身を確認
  const content = await Deno.readTextFile(path!);
  const parsed = JSON.parse(content);
  assertEquals(parsed.env.TEST, "true");
  
  // クリーンアップ
  await Deno.remove(tempDir, { recursive: true });
});

Deno.test("generateSettingsJson_空設定_ファイル生成しない", async () => {
  const tempDir = await Deno.makeTempDir();
  const settings = {};
  
  const path = await generateSettingsJson(settings, tempDir);
  
  assertEquals(path, undefined);
  
  // ディレクトリも作成されていないことを確認
  try {
    await Deno.stat(`${tempDir}/.claude`);
    throw new Error("Directory should not exist");
  } catch (error) {
    assertEquals(error instanceof Deno.errors.NotFound, true);
  }
  
  // クリーンアップ
  await Deno.remove(tempDir, { recursive: true });
});

// 統合テスト（実行可能スクリプトとして）
Deno.test("main_標準入出力_正しいJSON出力", async () => {
  const input: ConfigInput = {
    prompt: "Test task",
    mode: "readonly"
  };
  
  // config.tsを子プロセスとして実行
  const cmd = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-all", "./config.ts"],
    cwd: new URL(".", import.meta.url).pathname,
    stdin: "piped",
    stdout: "piped",
    stderr: "piped"
  });
  
  const process = cmd.spawn();
  
  // 入力を送信
  const writer = process.stdin.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(input)));
  await writer.close();
  
  // 出力を取得
  const { code, stdout, stderr } = await process.output();
  
  assertEquals(code, 0);
  
  const output: ConfigOutput = JSON.parse(new TextDecoder().decode(stdout));
  assertEquals(output.prompt, "Test task");
  assertEquals(output.sdkOptions.allowedTools, ["Read", "Glob", "Grep", "LS"]);
  assertExists(output.claudeId);
});

Deno.test("main_不正なモード_エラー出力", async () => {
  const input: ConfigInput = {
    prompt: "Test",
    mode: "invalid" as any
  };
  
  const cmd = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-all", "./config.ts"],
    cwd: new URL(".", import.meta.url).pathname,
    stdin: "piped",
    stdout: "piped",
    stderr: "piped"
  });
  
  const process = cmd.spawn();
  
  const writer = process.stdin.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(input)));
  await writer.close();
  
  const { code, stderr } = await process.output();
  
  assertEquals(code, 1);
  
  const error = JSON.parse(new TextDecoder().decode(stderr));
  assertEquals(error.code, "PRESET_NOT_FOUND");
});