import { assertEquals, assertStringIncludes } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { log, toJsonl } from "./core.ts";
import type { LogData } from "./types.ts";

// stdout出力をキャプチャするヘルパー
function captureStdout(fn: () => void): string {
  const originalLog = console.log;
  let output = "";
  console.log = (msg: string) => { output = msg; };
  try {
    fn();
    return output;
  } finally {
    console.log = originalLog;
  }
}

Deno.test("toJsonl - 辞書をJSON文字列に変換", () => {
  const testCases = [
    { input: { key: "value" }, expected: ["key"] },
    { input: { a: 1, b: "two" }, expected: ["a", "b"] },
    { input: { nested: { inner: "value" } }, expected: ["nested"] },
  ];

  for (const { input, expected } of testCases) {
    const result = toJsonl(input);
    const parsed = JSON.parse(result);
    
    // すべてのキーが保持されている
    for (const key of expected) {
      assertEquals(key in parsed, true);
    }
  }
});

Deno.test("toJsonl - 改行を含まない1行の文字列を生成", () => {
  const data = { key: "value", nested: { inner: "data" } };
  const result = toJsonl(data);
  
  assertEquals(result.includes("\n"), false);
  assertEquals(result.includes("\r"), false);
});

Deno.test("log - 2つの引数（level, data）を受け取る", () => {
  const output = captureStdout(() => {
    log("INFO", { uri: "/test", message: "test message" });
  });
  
  // エラーなく実行され、出力がある
  assertStringIncludes(output, "INFO");
});

Deno.test("log - stdoutに出力する（log = stdout原則）", () => {
  const testData: LogData = { uri: "/api/test", message: "test" };
  
  const output = captureStdout(() => {
    log("INFO", testData);
  });
  
  // 出力がある
  assertEquals(output.length > 0, true);
  assertStringIncludes(output, "INFO");
});

Deno.test("log - levelとdataの内容を含むJSONL形式で出力", () => {
  const testData: LogData = {
    uri: "/test/endpoint",
    message: "Test message",
    extra: "data",
  };
  
  const output = captureStdout(() => {
    log("ERROR", testData);
  });
  
  const parsed = JSON.parse(output);
  
  // levelが含まれている
  assertEquals(parsed.level, "ERROR");
  
  // dataの内容が展開されている
  assertEquals(parsed.uri, "/test/endpoint");
  assertEquals(parsed.message, "Test message");
  assertEquals(parsed.extra, "data");
});

Deno.test("log - 任意のログレベル文字列を使用可能", () => {
  const output1 = captureStdout(() => {
    log("METRIC", { uri: "/metrics", message: "Custom level" });
  });
  
  const output2 = captureStdout(() => {
    log("AUDIT", { uri: "/audit", message: "Audit log" });
  });
  
  assertStringIncludes(output1, "METRIC");
  assertStringIncludes(output2, "AUDIT");
});

Deno.test("LogData - 型定義が拡張可能", () => {
  // 拡張型の定義
  type AppLogData = LogData & {
    userId: string;
    requestId: string;
  };
  
  const data: AppLogData = {
    uri: "/api/users",
    message: "User created",
    userId: "123",
    requestId: "req-456",
  };
  
  // エラーなく使用可能
  const output = captureStdout(() => {
    log("INFO", data);
  });
  
  const parsed = JSON.parse(output);
  assertEquals(parsed.userId, "123");
  assertEquals(parsed.requestId, "req-456");
});