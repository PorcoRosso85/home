/**
 * シンプルClaude解析用Hook
 */

import { useState } from 'react';
import type { ClaudeAnalysisResult, NodeData } from '../../domain/types.ts';
import { createBasicRpcClient } from '../../infrastructure/rpc/basicRpcClient.ts';
import { generateVersionAnalysisPrompt } from './simplePromptGenerator.ts';
import { env } from '../../infrastructure/config/variables.ts';

type UseSimpleClaudeAnalysisReturn = {
  loading: boolean;
  result: string | null;
  error: string | null;
  analyzeVersion: (node: NodeData) => Promise<void>;
};

function useSimpleClaudeAnalysis(): UseSimpleClaudeAnalysisReturn {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // RPCクライアント初期化
  const rpcClient = createBasicRpcClient({
    endpoint: env.CLAUDE_WS_ENDPOINT,
    timeout: 60000 // 60秒（Claude解析は時間がかかる場合があるため）
  });
  
  const analyzeVersion = async (node: NodeData): Promise<void> => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      // プロンプト生成
      const prompt = generateVersionAnalysisPrompt(node);
      
      // Claude解析実行
      const analysisResult: ClaudeAnalysisResult = await rpcClient.sendClaudeRequest(prompt);
      
      // 結果処理（パターンマッチ）
      switch (analysisResult.status) {
        case "success":
          setResult(analysisResult.data);
          break;
        case "error":
          setError(analysisResult.message);
          break;
        default:
          // TypeScriptの網羅性チェック
          const _exhaustive: never = analysisResult;
          setError("Unknown error occurred");
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };
  
  return {
    loading,
    result,
    error,
    analyzeVersion
  };
}

export { useSimpleClaudeAnalysis };
export type { UseSimpleClaudeAnalysisReturn };
