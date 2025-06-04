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
  
  function sendCommand(command: string, args: string[] = []): Promise<ClaudeAnalysisResult> {
    logger.info('RPC リクエスト開始', {
      endpoint: config.endpoint,
      command,
      args,
      timeout: config.timeout
    });
    
    return new Promise((resolve) => {
      const ws = new WebSocket(config.endpoint);
      let accumulatedData = "";
      
      const timeoutId = setTimeout(() => {
        ws.close();
        logger.warn('RPC タイムアウト', { timeout: config.timeout });
        resolve({ 
          status: "error", 
          message: `Request timeout after ${config.timeout}ms` 
        });
      }, config.timeout);
      
      ws.onopen = () => {
        const message = {
          jsonrpc: "2.0",
          method: "exec",
          params: { command, args },
          id: Date.now()
        };
        ws.send(JSON.stringify(message));
        logger.debug('WebSocket メッセージ送信完了', { messageId: message.id });
      };
      
      ws.onmessage = (e) => {
        try {
          const res = JSON.parse(e.data);
          
          if (res.result?.stream) {
            accumulatedData += res.result.stdout;
            logger.debug('出力受信', {
              dataLength: res.result.stdout.length,
              totalLength: accumulatedData.length
            });
          } else if (res.result?.complete) {
            clearTimeout(timeoutId);
            logger.info('実行完了', {
              code: res.result.code,
              outputLength: accumulatedData.length
            });
            resolve({ 
              status: "success", 
              data: accumulatedData
            });
            ws.close();
          } else if (res.error) {
            clearTimeout(timeoutId);
            logger.error('実行エラー', { error: res.error });
            resolve({ 
              status: "error", 
              message: res.error.message || "Unknown error"
            });
            ws.close();
          }
        } catch (error) {
          logger.error('RPC パース エラー', { error: error instanceof Error ? error.message : 'Unknown' });
        }
      };
      
      ws.onerror = () => {
        clearTimeout(timeoutId);
        logger.error('RPC WebSocket エラー', { endpoint: config.endpoint });
        resolve({ 
          status: "error", 
          message: "WebSocket connection error" 
        });
      };
    });
  }
  
  return {
    sendCommand
  };
}

export { createBasicRpcClient };
export type { RpcConfig };
