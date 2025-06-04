/**
 * Claude Request Core Logic（Pure関数）
 */
import type { ClaudeAnalysisResult } from '../../domain/types';
import type { RpcConfig } from '../../infrastructure/rpc/basicRpcClient';
import { createBasicRpcClient } from '../../infrastructure/rpc/basicRpcClient';

export type ClaudeRequestInput = {
  prompt: string;
  rpcConfig: RpcConfig;
};

export type ClaudeRequestResult = 
  | { success: true; data: string }
  | { success: false; message: string };

/**
 * Claude リクエスト送信のCore Logic
 */
export const sendClaudeRequestCore = async (
  input: ClaudeRequestInput
): Promise<ClaudeRequestResult> => {
  try {
    const rpcClient = createBasicRpcClient(input.rpcConfig);
    
    // Claude-codeコマンドとしてプロンプトを実行
    const args = [
      "dlx", 
      "@anthropic-ai/claude-code", 
      "--dangerously-skip-permissions",
      "-p", 
      "--output-format", 
      "json", 
      input.prompt
    ];
    
    const analysisResult = await rpcClient.sendCommand("pnpm", args);
    
    if (analysisResult.status === 'success') {
      return { success: true, data: analysisResult.data };
    } else {
      return { success: false, message: analysisResult.message };
    }
  } catch (err) {
    return { 
      success: false, 
      message: err instanceof Error ? err.message : 'Unknown error' 
    };
  }
};

/**
 * プロンプト生成のCore Logic
 */
export type PromptGenerationInput = {
  action: string;
  nodeId?: string;
  nodeName?: string;
};

export type PromptGenerationOutput = {
  prompt: string;
};

export const generatePromptCore = (input: PromptGenerationInput): PromptGenerationOutput => {
  switch (input.action) {
    case 'connection-check':
      // RPC接続確認は別処理のため、ダミー値
      return { prompt: '' };
    case 'claude-boss-test':
      return {
        prompt: `あなたはclaude<id>です。あなたは親分です。あなたの子分ナンバリング方法を決めてください。その後、'pnpm dlx @anthropic-ai/claude-code -p <prompt>'を実行して、それぞれのclaude君に自身のナンバリング番号ただそれだけを返却させるよう子分に指示してください。最低3人の子分を作成してください。`
      };
    default:
      return { 
        prompt: `不明なアクション: ${input.action}` 
      };
  }
};

/**
 * RPC コマンド送信のCore Logic
 */
export const sendRpcCommandCore = async (
  command: string,
  args: string[],
  rpcConfig: RpcConfig
): Promise<ClaudeRequestResult> => {
  try {
    const rpcClient = createBasicRpcClient(rpcConfig);
    const result = await rpcClient.sendCommand(command, args);
    
    if (result.status === 'success') {
      return { success: true, data: result.data };
    } else {
      return { success: false, message: result.message };
    }
  } catch (error) {
    return { 
      success: false, 
      message: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
};
