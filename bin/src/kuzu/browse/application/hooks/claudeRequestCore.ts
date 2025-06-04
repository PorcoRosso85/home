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
  input: ClaudeRequestInput & { useTmux?: boolean; sessionName?: string }
): Promise<ClaudeRequestResult> => {
  try {
    const rpcClient = createBasicRpcClient(input.rpcConfig);
    
    // tmuxパラメータは無視して、常に通常のClaude-code実行
    const analysisResult = await rpcClient.sendClaudeRequest(input.prompt);
    
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
 * プロンプト生成のCore Logic（tmux削除）
 */
export const handleTmuxSessionCreated = (sessionName: string): void => {
  // tmux機能は削除されました
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
  sessionName?: string;
  useTmux?: boolean;
};

export const generatePromptCore = (input: PromptGenerationInput): PromptGenerationOutput => {
  switch (input.action) {
    case 'claude-analysis':
      return { 
        prompt: `バージョン${input.nodeId}の解析を行ってください。詳細: ${input.nodeName}`
      };
    case 'rust-hello':
      return { 
        prompt: '/home/nixos/bin/src/tmp/hello.rs\nここにhelloを返す関数とそれをコンソール出力するためのテストをインソーステストとして記述して'
      };
    case 'claude-code-echo':
      return {
        prompt: `他のclaude-codeを2つ呼び出して、'hello'のみを返却するプロンプトを送信して、hello2つを受け取ったら報告すること。hello以外を受け取った場合もその旨報告すること。claude-codeは "pnpm dlx @anthropic-ai/claude-code -p"に続きプロンプトを記入することで返答を受け取れる。`
      };
    case 'tmux-claude-echo':
      // tmux機能は削除されたため、通常のclaude-echoとして処理
      return {
        prompt: `echo "hello"を実行して、その出力を報告してください。`
      };
    default:
      return { 
        prompt: `不明なアクション: ${input.action}` 
      };
  }
};
