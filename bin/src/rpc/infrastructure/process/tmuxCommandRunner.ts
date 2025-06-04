// tmuxセッション作成と出力キャプチャ

import type { TmuxSessionParams, TmuxMessage } from "../../domain/command/tmuxTypes.ts";
import type { StreamMessage } from "../../domain/command/types.ts";

export async function* executeTmuxCommand(
  params: TmuxSessionParams
): AsyncGenerator<StreamMessage> {
  const { sessionName, command, args } = params;
  const outputFile = params.outputFile || `/tmp/tmux-${sessionName}-${Date.now()}.log`;
  
  console.log(`[tmuxCommandRunner] Creating tmux session: ${sessionName}`);
  console.log(`[tmuxCommandRunner] Output file: ${outputFile}`);
  
  // tmuxセッションを作成（出力をファイルにリダイレクト）
  // shを使用してリダイレクトを実行
  const shellCommand = `${command} ${args.join(" ")} 2>&1 | tee ${outputFile}`;
  const tmuxArgs = [
    "new-session",
    "-d",
    "-s", sessionName,
    "sh", "-c",
    shellCommand
  ];
  
  console.log(`[tmuxCommandRunner] Tmux command: tmux ${tmuxArgs.join(" ")}`);
  
  const tmuxCmd = new Deno.Command("tmux", {
    args: tmuxArgs,
    stdout: "piped",
    stderr: "piped",
  });
  
  const process = tmuxCmd.spawn();
  const { code } = await process.status;
  
  if (code !== 0) {
    const stderr = await process.stderr?.getReader().read();
    const errorMsg = stderr?.value ? new TextDecoder().decode(stderr.value) : "Unknown error";
    console.error(`[tmuxCommandRunner] Failed to create session: ${errorMsg}`);
    yield {
      type: "error",
      errorCode: "SESSION_ERROR",
      message: `Failed to create tmux session: ${errorMsg}`,
    };
    return;
  }
  
  console.log(`[tmuxCommandRunner] Session created successfully`);
  
  // セッション作成成功を通知
  yield {
    type: "chunk",
    data: JSON.stringify({
      type: "session_created",
      sessionName,
      outputFile,
    }),
  };
  
  // ファイルから出力を読み取ってストリーミング
  yield* streamFileContent(outputFile);
}

async function* streamFileContent(
  filePath: string
): AsyncGenerator<StreamMessage> {
  let lastPosition = 0;
  const decoder = new TextDecoder();
  let attempts = 0;
  const maxAttempts = 300; // 5分間（1秒ごとに300回）
  let fileExists = false;
  let noNewDataCount = 0;
  const maxNoNewDataCount = 30; // 30秒間新しいデータがなければ終了（claude-codeの処理時間を考慮）
  let lastContent = "";
  let hasReceivedAnyData = false; // データを一度でも受信したか
  
  console.log(`[streamFileContent] Starting to monitor file: ${filePath}`);
  
  // 初回は少し待機（tmuxセッションが開始されるまで）
  await new Promise(resolve => setTimeout(resolve, 2000)); // 2秒待機
  
  while (attempts < maxAttempts) {
    try {
      // ファイル全体を読み取る（サイズが小さいため）
      const content = await Deno.readTextFile(filePath);
      
      if (!fileExists) {
        fileExists = true;
        console.log(`[streamFileContent] File found: ${filePath}`);
      }
      
      if (content.length > lastContent.length) {
        // 新しいデータがある
        noNewDataCount = 0;
        hasReceivedAnyData = true;
        const newData = content.substring(lastContent.length);
        console.log(`[streamFileContent] New data (${newData.length} chars)`);
        
        yield {
          type: "chunk",
          data: newData,
        };
        
        lastContent = content;
        
        // JSON出力が完了したかチェック（claude-codeの出力形式）
        try {
          const parsed = JSON.parse(content);
          if (parsed.type === "result" && (parsed.subtype === "success" || parsed.is_error)) {
            console.log(`[streamFileContent] Claude-code execution completed`);
            yield {
              type: "complete",
              code: 0,
            };
            break;
          }
        } catch {
          // JSONパースエラーは無視（まだ完全なJSONではない可能性）
        }
      } else if (fileExists) {
        // ファイルは存在するが新しいデータがない
        noNewDataCount++;
        
        // 初回データ待ちの場合はより長く待つ
        const waitThreshold = hasReceivedAnyData ? maxNoNewDataCount : 60; // 初回は60秒待つ
        
        if (noNewDataCount >= waitThreshold) {
          console.log(`[streamFileContent] No new data for ${waitThreshold} seconds, completing`);
          
          // 最後に残っているデータがあれば送信
          if (lastContent.length === 0 && content.length > 0) {
            console.log(`[streamFileContent] Sending final content (${content.length} chars)`);
            yield {
              type: "chunk",
              data: content,
            };
          }
          
          yield {
            type: "complete",
            code: 0,
          };
          break;
        }
      }
      
    } catch (error) {
      // ファイルがまだ存在しない場合は待機を続ける
      if (!fileExists && attempts < 30) {
        console.log(`[streamFileContent] Waiting for file creation (attempt ${attempts + 1})`);
      } else if (fileExists && error.message.includes("No such file")) {
        console.log(`[streamFileContent] File deleted, completing`);
        yield {
          type: "complete",
          code: 0,
        };
        break;
      } else if (attempts > 30 && !fileExists) {
        console.error(`[streamFileContent] File not created after 30 seconds`);
        yield {
          type: "error",
          errorCode: "OUTPUT_ERROR",
          message: `Output file not created: ${filePath}`,
        };
        return;
      } else {
        console.error(`[streamFileContent] Error reading file: ${error.message}`);
      }
    }
    
    // 1秒待機
    await new Promise(resolve => setTimeout(resolve, 1000));
    attempts++;
  }
  
  if (attempts >= maxAttempts) {
    console.log(`[streamFileContent] Max attempts reached, completing`);
    yield {
      type: "complete",
      code: 0,
    };
  }
}
