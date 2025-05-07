// kuzu/terminal/serve/executor.ts

import { CLI_PATH } from "./constants.ts";

/**
 * CLIコマンドを実行し、ストリーミングのためのリーダブルストリームを返す
 * @param command 実行するコマンド
 * @param args コマンド引数
 * @param stdin 標準入力データ（オプション）
 * @returns {stdout, stderr, process} 標準出力/エラー用リーダーとプロセス
 */
export async function executeCommand(
  command: string, 
  args: string[] = [], 
  stdin: string = ""
): Promise<{
  stdout: ReadableStream<Uint8Array>;
  stderr: ReadableStream<Uint8Array>;
  process: Deno.Process;
}> {
  try {
    console.log(`実行するコマンド: ${command} ${args.join(' ')}`);
    
    // 直接コマンドを実行
    const process = Deno.run({
      cmd: [command, ...args],
      stdin: "piped",
      stdout: "piped",
      stderr: "piped",
    });

    console.log(`プロセス開始 PID: ${process.pid}`);

    // 入力データがある場合は標準入力に書き込む
    if (stdin) {
      const encoder = new TextEncoder();
      await process.stdin.write(encoder.encode(stdin));
      process.stdin.close();
    } else {
      process.stdin.close();
    }

    // stdout と stderrをReadableStreamに変換
    const stdout = process.stdout.readable;
    const stderr = process.stderr.readable;

    return { stdout, stderr, process };
  } catch (error) {
    console.error(`コマンド実行エラー: ${error.message}`);
    console.error(`スタックトレース: ${error.stack}`);
    throw error;
  }
}
