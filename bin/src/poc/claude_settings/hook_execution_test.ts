import { assertEquals, assertStringIncludes } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { ensureDir, exists } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { getClaudeCommand, createSettings } from "./test_utils.ts";

Deno.test("hook: PreToolUseフックが実行される", async () => {
  const testDir = await Deno.makeTempDir();
  const settingsDir = `${testDir}/.claude`;
  const logFile = `${testDir}/hook_executed.log`;
  await ensureDir(settingsDir);
  
  // フック付き設定を作成
  const settingsWithHook = {
    hooks: {
      PreToolUse: [{
        matcher: ".*",
        hooks: [{
          type: "command",
          command: `echo "Hook executed at $(date)" > ${logFile}`
        }]
      }]
    }
  };
  
  await Deno.writeTextFile(
    `${settingsDir}/settings.json`,
    JSON.stringify(settingsWithHook, null, 2)
  );
  
  // Claude CLIを実行
  const cmd = new Deno.Command("claude", {
    args: ["--print", "現在のディレクトリの内容を表示して"],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process = cmd.spawn();
  await process.output();
  
  // フックが実行されたことを確認
  const hookExecuted = await exists(logFile);
  assertEquals(hookExecuted, true);
  
  if (hookExecuted) {
    const logContent = await Deno.readTextFile(logFile);
    assertStringIncludes(logContent, "Hook executed at");
  }
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("hook: 設定ごとに異なるフックが実行される", async () => {
  const testDir1 = await Deno.makeTempDir();
  const testDir2 = await Deno.makeTempDir();
  const settingsDir1 = `${testDir1}/.claude`;
  const settingsDir2 = `${testDir2}/.claude`;
  await ensureDir(settingsDir1);
  await ensureDir(settingsDir2);
  
  // プロジェクト1の設定：IDを記録
  const settings1 = {
    hooks: {
      Stop: [{
        matcher: "",
        hooks: [{
          type: "command",
          command: `echo "Project1 completed" > ${testDir1}/project_id.txt`
        }]
      }]
    }
  };
  
  // プロジェクト2の設定：異なるIDを記録
  const settings2 = {
    hooks: {
      Stop: [{
        matcher: "",
        hooks: [{
          type: "command",
          command: `echo "Project2 completed" > ${testDir2}/project_id.txt`
        }]
      }]
    }
  };
  
  await Deno.writeTextFile(
    `${settingsDir1}/settings.json`,
    JSON.stringify(settings1, null, 2)
  );
  
  await Deno.writeTextFile(
    `${settingsDir2}/settings.json`,
    JSON.stringify(settings2, null, 2)
  );
  
  // プロジェクト1でClaude実行
  const cmd1 = new Deno.Command("claude", {
    args: ["--print", "Hello"],
    cwd: testDir1,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process1 = cmd1.spawn();
  await process1.output();
  
  // プロジェクト2でClaude実行
  const cmd2 = new Deno.Command("claude", {
    args: ["--print", "Hello"],
    cwd: testDir2,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process2 = cmd2.spawn();
  await process2.output();
  
  // 各プロジェクトで正しいフックが実行されたことを確認
  const project1Id = await Deno.readTextFile(`${testDir1}/project_id.txt`);
  const project2Id = await Deno.readTextFile(`${testDir2}/project_id.txt`);
  
  assertStringIncludes(project1Id, "Project1");
  assertStringIncludes(project2Id, "Project2");
  
  // クリーンアップ
  await Deno.remove(testDir1, { recursive: true });
  await Deno.remove(testDir2, { recursive: true });
});

Deno.test("hook: フックによるツール使用のブロック", async () => {
  const testDir = await Deno.makeTempDir();
  const settingsDir = `${testDir}/.claude`;
  const blockLog = `${testDir}/blocked.log`;
  await ensureDir(settingsDir);
  
  // Bashコマンドをブロックするフック
  const blockingHookSettings = {
    hooks: {
      PreToolUse: [{
        matcher: "Bash",
        hooks: [{
          type: "command",
          command: `echo "Bash command blocked" > ${blockLog} && exit 2`
        }]
      }]
    }
  };
  
  await Deno.writeTextFile(
    `${settingsDir}/settings.json`,
    JSON.stringify(blockingHookSettings, null, 2)
  );
  
  // Bashコマンドを実行しようとする
  const cmd = new Deno.Command("claude", {
    args: ["--print", "echo 'test' を実行して"],
    cwd: testDir,
    stdout: "piped",
    stderr: "piped"
  });
  
  const process = cmd.spawn();
  const { code, stderr } = await process.output();
  const error = new TextDecoder().decode(stderr);
  
  // ブロックされたことを確認
  assertEquals(code, 1);
  assertStringIncludes(error, "blocked");
  
  // ブロックログが作成されたことを確認
  const blocked = await exists(blockLog);
  assertEquals(blocked, true);
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});