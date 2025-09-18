import { assertEquals, assertStringIncludes } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { ensureDir, exists } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { getClaudeCommand, createSettings } from "./test_utils.ts";

Deno.test("permission: 読み取り専用モードではWriteツールがブロックされる", async () => {
  const testDir = await Deno.makeTempDir();
  
  // 読み取り専用設定を作成
  const readOnlySettings = {
    allowedTools: ["Read", "Glob", "Grep", "LS"]
  };
  
  await createSettings(testDir, readOnlySettings);
  
  // Claude SDKを呼び出し
  const claudeCmd = await getClaudeCommand();
  const cmd = new Deno.Command(claudeCmd[0], {
    args: [...claudeCmd.slice(1), "--claude-id", "test-readonly", "--uri", testDir, "--print", "test.txtというファイルを作成してください"],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process = cmd.spawn();
  const { code, stdout, stderr } = await process.output();
  
  const output = new TextDecoder().decode(stdout);
  const error = new TextDecoder().decode(stderr);
  
  // Writeツールの使用がブロックされることを確認
  assertStringIncludes(error, "Write tool is not allowed");
  assertEquals(code, 1);
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("permission: 権限昇格フラグで書き込みが可能になる", async () => {
  const testDir = await Deno.makeTempDir();
  
  // フル権限設定を作成
  const fullPermissionSettings = {
    allowedTools: ["Read", "Write", "Edit", "MultiEdit", "Bash", "Glob", "Grep", "LS"]
  };
  
  await createSettings(testDir, fullPermissionSettings);
  
  // Claude SDKを呼び出し
  const claudeCmd = await getClaudeCommand();
  const cmd = new Deno.Command(claudeCmd[0], {
    args: [...claudeCmd.slice(1), "--claude-id", "test-fullperm", "--uri", testDir, "--allow-write", "--print", "test.txtというファイルを作成してください"],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process = cmd.spawn();
  const { code } = await process.output();
  
  // 成功することを確認
  assertEquals(code, 0);
  
  // ファイルが作成されたことを確認
  const fileExists = await exists(`${testDir}/test.txt`);
  assertEquals(fileExists, true);
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("permission: settings.jsonの動的更新が反映される", async () => {
  const testDir = await Deno.makeTempDir();
  const claudeCmd = await getClaudeCommand();

  // 初期設定：読み取り専用
  await createSettings(testDir, { allowedTools: ["Read"] });

  // 最初の実行：失敗することを確認
  const cmd1 = new Deno.Command(claudeCmd[0], {
    args: [...claudeCmd.slice(1), "--claude-id", "test-dynamic1", "--uri", testDir, "--print", "ファイルを作成して"],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process1 = cmd1.spawn();
  const result1 = await process1.output();
  assertEquals(result1.code, 1);
  
  // 設定を更新：書き込み権限を追加
  await createSettings(testDir, { allowedTools: ["Read", "Write"] });
  
  // 2回目の実行：成功することを確認
  const cmd2 = new Deno.Command(claudeCmd[0], {
    args: [...claudeCmd.slice(1), "--claude-id", "test-dynamic2", "--uri", testDir, "--allow-write", "--print", "ファイルを作成して"],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process2 = cmd2.spawn();
  const result2 = await process2.output();
  assertEquals(result2.code, 0);
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});