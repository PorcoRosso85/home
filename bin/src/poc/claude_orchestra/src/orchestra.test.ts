import { assertEquals, assertStringIncludes } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { exists } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { runPipeline } from "./helpers.ts";

// TDD Red: これらのテストは現時点で失敗することが期待される

Deno.test("orchestra_readonly_ファイル作成拒否", async () => {
  const testDir = await Deno.makeTempDir();
  
  // 1. 設定生成 (claude_config)
  const configInput = {
    prompt: "Create a new file test.txt",
    mode: "readonly",
    workdir: testDir
  };
  
  const configCmd = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-all", "../claude_config/src/config.ts"],
    stdin: "piped",
    stdout: "piped",
    stderr: "piped"
  });
  
  const configProcess = configCmd.spawn();
  const writer = configProcess.stdin.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(configInput)));
  await writer.close();
  
  const { stdout: configOutput } = await configProcess.output();
  const config = JSON.parse(new TextDecoder().decode(configOutput));
  
  // 2. SDK実行 (claude_sdk)
  const sdkCmd = new Deno.Command(Deno.execPath(), {
    args: [
      "run", "--allow-all", "../claude_sdk/claude.ts",
      "--claude-id", config.claudeId,
      "--uri", config.workdir,
      "--print", config.prompt
    ],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const sdkProcess = sdkCmd.spawn();
  const { code, stderr } = await sdkProcess.output();
  const errorOutput = new TextDecoder().decode(stderr);
  
  // 3. 検証: Writeツールがブロックされることを確認
  assertStringIncludes(errorOutput, "not allowed");
  assertEquals(code, 1);
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("orchestra_production_危険コマンドブロック", async () => {
  const testDir = await Deno.makeTempDir();
  
  // 1. Production設定生成
  const configInput = {
    prompt: "Run rm -rf /tmp/test",
    mode: "production",
    workdir: testDir
  };
  
  const configCmd = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-all", "../claude_config/src/config.ts"],
    stdin: "piped",
    stdout: "piped"
  });
  
  const configProcess = configCmd.spawn();
  const writer = configProcess.stdin.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(configInput)));
  await writer.close();
  
  const { stdout: configOutput } = await configProcess.output();
  const config = JSON.parse(new TextDecoder().decode(configOutput));
  
  // settings.jsonが生成されていることを確認
  const settingsExists = await exists(`${testDir}/.claude/settings.json`);
  assertEquals(settingsExists, true);
  
  // settings.jsonの内容を確認
  const settings = JSON.parse(await Deno.readTextFile(`${testDir}/.claude/settings.json`));
  assertStringIncludes(settings.permissions.deny.join(" "), "rm:");
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("orchestra_development_全機能動作", async () => {
  const testDir = await Deno.makeTempDir();
  
  // 1. Development設定生成
  const configInput = {
    prompt: "Create and edit files",
    mode: "development",
    workdir: testDir
  };
  
  const configCmd = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-all", "../claude_config/src/config.ts"],
    stdin: "piped",
    stdout: "piped"
  });
  
  const configProcess = configCmd.spawn();
  const writer = configProcess.stdin.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(configInput)));
  await writer.close();
  
  const { stdout: configOutput } = await configProcess.output();
  const config = JSON.parse(new TextDecoder().decode(configOutput));
  
  // 開発モードではすべてのツールが許可される
  assertEquals(config.sdkOptions.allowedTools, ["*"]);
  assertEquals(config.sdkOptions.permissionMode, "acceptEdits");
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("orchestra_error_config失敗時中断", async () => {
  // 不正なモードでconfig実行
  const configInput = {
    prompt: "Test",
    mode: "invalid_mode"
  };
  
  const configCmd = new Deno.Command(Deno.execPath(), {
    args: ["run", "--allow-all", "../claude_config/src/config.ts"],
    stdin: "piped",
    stdout: "piped",
    stderr: "piped"
  });
  
  const configProcess = configCmd.spawn();
  const writer = configProcess.stdin.getWriter();
  await writer.write(new TextEncoder().encode(JSON.stringify(configInput)));
  await writer.close();
  
  const { code, stderr } = await configProcess.output();
  const errorOutput = new TextDecoder().decode(stderr);
  const error = JSON.parse(errorOutput);
  
  // configが失敗することを確認
  assertEquals(code, 1);
  assertEquals(error.code, "PRESET_NOT_FOUND");
  
  // この場合、SDKは実行されるべきではない（パイプラインが中断）
});