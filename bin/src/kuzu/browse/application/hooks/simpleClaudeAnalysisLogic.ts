import type { 
  ClaudeAnalysisResult
} from '../../domain/types';
import type { 
  ClaudeAnalysisSuccess,
  ClaudeAnalysisError
} from '../types/claudeTypes';
import { createError, createSuccess } from '../../common/errorHandler';
import { generateVersionAnalysisPrompt } from '../claude/simplePromptGenerator';

// Claude解析機能の入力型
export type SimpleClaudeAnalysisInput = {
  node: any;
  rpcClient: {
    sendClaudeRequest: (prompt: string) => Promise<ClaudeAnalysisResult>;
  };
};

// Claude解析機能の結果型（CONVENTION.yaml準拠）
export type SimpleClaudeAnalysisResult = ClaudeAnalysisSuccess | ClaudeAnalysisError;

/**
 * Claude解析Core関数（Pure Logic）
 * CONVENTION.yaml準拠: Result型使用禁止、個別Tagged Union使用
 */
export const executeClaudeAnalysisCore = async (input: SimpleClaudeAnalysisInput): Promise<SimpleClaudeAnalysisResult> => {
  // Core層：プロンプト生成（try/catch除去済み）
  const prompt = generateVersionAnalysisPrompt(input.node);
  
  // Core層：Claude解析実行
  const analysisResult: ClaudeAnalysisResult = await input.rpcClient.sendClaudeRequest(prompt);
  
  // Core層：結果処理（明示的分岐 - パターンマッチ）
  switch (analysisResult.status) {
    case "success":
      return { status: "success", data: analysisResult.data };
    case "error":
      return { status: "error", message: analysisResult.message };
    default:
      // 網羅性チェック
      const _exhaustive: never = analysisResult;
      return { status: "error", message: "未処理の解析ケース" };
  }
};
