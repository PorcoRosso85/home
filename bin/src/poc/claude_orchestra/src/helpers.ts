/**
 * Orchestra Test Helpers - テスト用のユーティリティ関数
 */

import type { ConfigOutput } from "./types.ts";

/**
 * claude_configを実行して設定を生成
 */
export async function runConfig(input: {
  prompt: string;
  mode: string;
  workdir?: string;
}): Promise<{ success: boolean; output?: ConfigOutput; error?: string }> {
  try {
    const configPath = "../claude_config/src/config.ts";
    
    const cmd = new Deno.Command(Deno.execPath(), {
      args: ["run", "--allow-all", configPath],
      stdin: "piped",
      stdout: "piped",
      stderr: "piped"
    });
    
    const process = cmd.spawn();
    const writer = process.stdin.getWriter();
    await writer.write(new TextEncoder().encode(JSON.stringify(input)));
    await writer.close();
    
    const { code, stdout, stderr } = await process.output();
    
    if (code !== 0) {
      const error = new TextDecoder().decode(stderr);
      return { success: false, error };
    }
    
    const output = JSON.parse(new TextDecoder().decode(stdout));
    return { success: true, output };
    
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

/**
 * claude_sdkを実行
 */
export async function runSdk(config: ConfigOutput): Promise<{
  success: boolean;
  stdout?: string;
  stderr?: string;
  code: number;
}> {
  try {
    const sdkPath = "../claude_sdk/claude.ts";
    
    const args = [
      "run", "--allow-all", sdkPath,
      "--claude-id", config.claudeId,
      "--uri", config.workdir,
      "--print", config.prompt
    ];
    
    // sdkOptionsに基づいて追加の引数を設定
    if (config.sdkOptions.allowedTools?.includes("*")) {
      args.push("--allow-write");
    }
    
    const cmd = new Deno.Command(Deno.execPath(), {
      args,
      cwd: config.workdir,
      stdout: "piped",
      stderr: "piped"
    });
    
    const process = cmd.spawn();
    const { code, stdout, stderr } = await process.output();
    
    return {
      success: code === 0,
      code,
      stdout: new TextDecoder().decode(stdout),
      stderr: new TextDecoder().decode(stderr)
    };
    
  } catch (error) {
    return {
      success: false,
      code: -1,
      stderr: String(error)
    };
  }
}

/**
 * パイプライン全体を実行
 */
export async function runPipeline(input: {
  prompt: string;
  mode: string;
  workdir: string;
}): Promise<{
  configResult: Awaited<ReturnType<typeof runConfig>>;
  sdkResult?: Awaited<ReturnType<typeof runSdk>>;
}> {
  // 1. Config実行
  const configResult = await runConfig(input);
  
  if (!configResult.success || !configResult.output) {
    return { configResult };
  }
  
  // 2. SDK実行
  const sdkResult = await runSdk(configResult.output);
  
  return { configResult, sdkResult };
}