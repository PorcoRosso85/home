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
  
  return {
    sendClaudeRequest
  };
}

export { createBasicRpcClient };
export type { RpcConfig };
