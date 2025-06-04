/**
 * 基本RPC通信クライアント
 */

import type { ClaudeAnalysisResult } from '../../domain/types.ts';
import * as logger from '../../../common/infrastructure/logger.ts';

type RpcConfig = {
  endpoint: string;
  timeout: number;
};

function createBasicRpcClient(config: RpcConfig) {
  
  function sendClaudeRequest(prompt: string, data?: any): Promise<ClaudeAnalysisResult> {
    // DevTools にリクエスト詳細をログ出力
    logger.info('Claude RPC リクエスト開始', {
      endpoint: config.endpoint,
      promptPreview: prompt.substring(0, 100) + (prompt.length > 100 ? '...' : ''),
      fullPromptLength: prompt.length,
      timeout: config.timeout
    });
    
    return new Promise((resolve) => {
      const ws = new WebSocket(config.endpoint);
      let accumulatedData = "";
      
      const args = [
        "dlx", 
        "@anthropic-ai/claude-code", 
        "--dangerously-skip-permissions",
        "-p", 
        "--output-format", 
        "json", 
        prompt
      ];
      
      // リクエストコマンドもログ出力
      logger.debug('Claude Code コマンド', {
        command: "pnpm",
        args: args
      });
      
      const timeoutId = setTimeout(() => {
        ws.close();
        logger.warn('Claude RPC タイムアウト', { timeout: config.timeout });
        resolve({ 
          status: "error", 
          message: `Request timeout after ${config.timeout}ms` 
        });
      }, config.timeout);
      
      ws.onopen = () => {
        const message = {
          jsonrpc: "2.0",
          method: "exec",
          params: { 
            command: "pnpm",
            args: args
          },
          id: Date.now()
        };
        ws.send(JSON.stringify(message));
        logger.debug('WebSocket メッセージ送信完了', { messageId: message.id });
      };
      
      ws.onmessage = (e) => {
        try {
          const res = JSON.parse(e.data);
          
          if (res.result?.stream) {
            // ストリーミングデータを蓄積
            accumulatedData += res.result.stdout;
            logger.debug('Claude出力受信', {
              chunkLength: res.result.stdout.length,
              totalLength: accumulatedData.length
            });
          } else if (res.result?.complete) {
            // 完了時
            clearTimeout(timeoutId);
            logger.info('Claude実行完了', {
              code: res.result.code,
              outputLength: accumulatedData.length,
              outputPreview: accumulatedData.substring(0, 200) + (accumulatedData.length > 200 ? '...' : '')
            });
            
            resolve({ 
              status: "success", 
              data: accumulatedData 
            });
            ws.close();
          } else if (res.error) {
            // エラー時
            clearTimeout(timeoutId);
            logger.error('Claude実行エラー', { error: res.error });
            resolve({ 
              status: "error", 
              message: res.error.message || "Unknown error"
            });
            ws.close();
          }
        } catch (error) {
          logger.error('Claude RPC パース エラー', { error: error instanceof Error ? error.message : 'Unknown' });
        }
      };
      
      ws.onerror = () => {
        clearTimeout(timeoutId);
        logger.error('Claude RPC WebSocket エラー', { endpoint: config.endpoint });
        resolve({ 
          status: "error", 
          message: "WebSocket connection failed" 
        });
      };
    });
  }
  
  function sendClaudeRequestInTmux(sessionName: string, prompt: string): Promise<ClaudeAnalysisResult> {
    logger.info('tmux内でClaude RPC リクエスト開始', {
      endpoint: config.endpoint,
      sessionName: sessionName,
      promptPreview: prompt.substring(0, 100) + (prompt.length > 100 ? '...' : ''),
      timeout: config.timeout
    });
    
    return new Promise((resolve) => {
      const ws = new WebSocket(config.endpoint);
      let accumulatedData = "";
      let outputFile = "";
      
      const args = [
        "new-session",
        "-d",
        "-s",
        sessionName,
        "pnpm",
        "dlx",
        "@anthropic-ai/claude-code",
        "--dangerously-skip-permissions",
        "-p",
        "--output-format",
        "json",
        prompt
      ];
      
      logger.debug('tmux コマンド', {
        command: "tmux",
        args: args
      });
      
      const timeoutId = setTimeout(() => {
        ws.close();
        logger.warn('tmux RPC タイムアウト', { timeout: config.timeout });
        resolve({ 
          status: "error", 
          message: `Request timeout after ${config.timeout}ms` 
        });
      }, config.timeout);
      
      ws.onopen = () => {
        const message = {
          jsonrpc: "2.0",
          method: "exec",
          params: { 
            command: "tmux",
            args: args
          },
          id: Date.now()
        };
        ws.send(JSON.stringify(message));
        logger.debug('tmux WebSocket メッセージ送信完了', { messageId: message.id });
      };
      
      ws.onmessage = (e) => {
        try {
          const res = JSON.parse(e.data);
          
          // デバッグ: 受信したメッセージをログ出力
          logger.debug('tmux WebSocket メッセージ受信', {
            hasResult: !!res.result,
            hasError: !!res.error,
            isStream: res.result?.stream,
            isComplete: res.result?.complete,
            dataLength: res.result?.stdout?.length || 0
          });
          
          if (res.result?.stream) {
            // ストリーミングデータを処理
            const data = res.result.stdout;
            
            // セッション作成メッセージをチェック
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === "session_created") {
                outputFile = parsed.outputFile;
                logger.info('tmuxセッション作成成功', {
                  sessionName: parsed.sessionName,
                  outputFile: outputFile
                });
                // session_createdメッセージはaccumulatedDataに追加しない
                return;
              }
            } catch {
              // JSONパースできない場合は通常の出力データとして処理
            }
            
            // 通常の出力データ
            accumulatedData += data;
            logger.debug('tmux出力受信', {
              dataLength: data.length,
              totalLength: accumulatedData.length,
              dataPreview: data.substring(0, 100)
            });
          } else if (res.result?.complete) {
            // 完了時
            clearTimeout(timeoutId);
            logger.info('tmux実行完了', {
              code: res.result.code,
              outputLength: accumulatedData.length,
              outputFile: outputFile
            });
            
            resolve({ 
              status: "success", 
              data: accumulatedData || `tmuxセッション '${sessionName}' でClaude-codeを実行しました。\n出力ファイル: ${outputFile}`
            });
            
            // デバッグ: 受信したデータの内容を確認
            if (accumulatedData) {
              try {
                const parsedData = JSON.parse(accumulatedData);
                logger.info('Claude-code実行結果', {
                  type: parsedData.type,
                  subtype: parsedData.subtype,
                  isError: parsedData.is_error,
                  resultPreview: parsedData.result?.substring(0, 200) + '...',
                  cost: parsedData.cost_usd,
                  duration: parsedData.duration_ms
                });
              } catch {
                logger.info('Claude-code出力（非JSON）', {
                  dataPreview: accumulatedData.substring(0, 200) + '...'
                });
              }
            }
            
            ws.close();
          } else if (res.error) {
            // エラー時
            clearTimeout(timeoutId);
            logger.error('tmux実行エラー', { error: res.error });
            resolve({ 
              status: "error", 
              message: res.error.message || "Unknown error"
            });
            ws.close();
          }
        } catch (error) {
          logger.error('tmux RPC パース エラー', { error: error instanceof Error ? error.message : 'Unknown' });
        }
      };
      
      ws.onerror = () => {
        clearTimeout(timeoutId);
        logger.error('tmux RPC WebSocket エラー', { endpoint: config.endpoint });
        resolve({ 
          status: "error", 
          message: "WebSocket connection error" 
        });
      };
    });
  }
  
  return {
    sendClaudeRequest,
    sendClaudeRequestInTmux
  };
}

export { createBasicRpcClient };
export type { RpcConfig };
