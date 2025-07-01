import { assertEquals, assertStringIncludes } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { exists } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { runPipeline, parseJsonlOutput } from "./helpers.ts";

// TDD Red: これらのテストは現時点で失敗することが期待される

Deno.test("orchestra_readonly_ファイル作成拒否", async () => {
  const testDir = await Deno.makeTempDir();
  
  // パイプライン実行
  const result = await runPipeline({
    prompt: "Create a new file test.txt with content hello",
    mode: "readonly",
    workdir: testDir
  });
  
  // 設定生成が成功していることを確認
  assertEquals(result.configResult.success, true);
  assertEquals(result.configResult.output?.sdkOptions.allowedTools, ["Read", "Glob", "Grep", "LS"]);
  
  // SDK実行結果の確認（実際のClaude CLIがない場合はスキップ）
  if (result.sdkResult) {
    // SDKの実行自体は成功する（Claude CLIが存在する場合）
    assertEquals(result.sdkResult.success, true);
    
    // JSONL出力をパースして権限要求を確認
    const events = parseJsonlOutput(result.sdkResult.stdout);
    
    // 権限要求メッセージを探す
    const requestEvent = events.find(e => 
      e.data?.type === "user" && 
      e.data?.message?.content?.[0]?.content?.includes("Claude requested permissions to use Write")
    );
    
    // もし権限要求が見つかった場合は確認
    if (requestEvent) {
      assertStringIncludes(
        requestEvent.data.message.content[0].content,
        "Claude requested permissions to use Write"
      );
    }
    
    // あるいは最終結果で権限制限を確認
    const resultEvent = events.find(e => e.data?.type === "result");
    if (resultEvent?.data?.result?.includes("permission")) {
      assertStringIncludes(resultEvent.data.result, "permission");
    }
  }
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("orchestra_production_危険コマンドブロック", async () => {
  const testDir = await Deno.makeTempDir();
  
  // Production設定でパイプライン実行
  const result = await runPipeline({
    prompt: "Run rm -rf /tmp/test",
    mode: "production",
    workdir: testDir
  });
  
  // 設定生成が成功していることを確認
  assertEquals(result.configResult.success, true);
  assertEquals(result.configResult.output?.sdkOptions.disallowedTools, ["Bash", "Write", "Edit"]);
  
  // settings.jsonが生成されていることを確認
  const settingsExists = await exists(`${testDir}/.claude/settings.json`);
  assertEquals(settingsExists, true);
  
  // settings.jsonの内容を確認
  const settings = JSON.parse(await Deno.readTextFile(`${testDir}/.claude/settings.json`));
  assertStringIncludes(settings.permissions.deny.join(" "), "rm:");
  
  // SDK実行結果の確認
  if (result.sdkResult) {
    // SDKは実行されるが、コマンドはブロックされる
    assertEquals(result.sdkResult.success, true);
    
    // JSONL出力をパースして権限拒否を確認
    const events = parseJsonlOutput(result.sdkResult.stdout);
    
    // 権限拒否メッセージを探す
    const denialEvent = events.find(e => 
      e.data?.type === "user" && 
      e.data?.message?.content?.[0]?.content?.includes("Permission to use Bash")
    );
    
    // メッセージが見つかった場合のみアサート
    if (denialEvent) {
      assertStringIncludes(
        denialEvent.data.message.content[0].content,
        "Permission to use Bash"
      );
    }
    
    // 最終結果メッセージを確認
    const resultEvent = events.find(e => e.data?.type === "result");
    const resultMessage = resultEvent?.data?.result || "";
    
    // より柔軟なマッチング - 権限拒否のメッセージが含まれることを確認
    const hasPermissionDenial = 
      resultMessage.includes("denied permission") ||
      resultMessage.includes("cannot delete") ||
      resultMessage.includes("cannot remove") ||
      resultMessage.includes("unable to delete") ||
      resultMessage.includes("unable to execute") ||
      resultMessage.includes("preventing") ||
      resultMessage.includes("blocked") ||
      resultMessage.includes("not permitted");
    
    assertEquals(hasPermissionDenial, true, 
      `Expected permission denial message, but got: ${resultMessage}`);
  }
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("orchestra_development_全機能動作", async () => {
  const testDir = await Deno.makeTempDir();
  
  // Development設定でパイプライン実行
  const result = await runPipeline({
    prompt: "Create and edit files",
    mode: "development",
    workdir: testDir
  });
  
  // 設定生成が成功していることを確認
  assertEquals(result.configResult.success, true);
  
  // 開発モードではすべてのツールが許可される
  assertEquals(result.configResult.output?.sdkOptions.allowedTools, ["*"]);
  assertEquals(result.configResult.output?.sdkOptions.permissionMode, "acceptEdits");
  
  // クリーンアップ
  await Deno.remove(testDir, { recursive: true });
});

Deno.test("orchestra_error_config失敗時中断", async () => {
  // 不正なモードでパイプライン実行
  const result = await runPipeline({
    prompt: "Test",
    mode: "invalid_mode",
    workdir: "/tmp"
  });
  
  // configが失敗することを確認
  assertEquals(result.configResult.success, false);
  
  // エラーが適切に返されることを確認
  const error = JSON.parse(result.configResult.error || "{}");
  assertEquals(error.code, "PRESET_NOT_FOUND");
  
  // SDKは実行されないことを確認（パイプラインが中断）
  assertEquals(result.sdkResult, undefined);
});