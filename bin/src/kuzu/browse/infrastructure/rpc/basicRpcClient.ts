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
      
      const args = [
        "dlx", 
        "@anthropic-ai/claude-code", 
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
        clearTimeout(timeoutId);
        try {
          const res = JSON.parse(e.data);
          const output = res.result?.stdout || res.error?.message || "No output";
          
          logger.info('Claude RPC レスポンス受信', {
            success: !!res.result,
            outputLength: output.length,
            outputPreview: output.substring(0, 200) + (output.length > 200 ? '...' : '')
          });
          
          resolve({ 
            status: "success", 
            data: output 
          });
        } catch (error) {
          logger.error('Claude RPC パース エラー', { error: error instanceof Error ? error.message : 'Unknown' });
          resolve({ 
            status: "error", 
            message: error instanceof Error ? error.message : "Parse error"
          });
        }
        ws.close();
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
