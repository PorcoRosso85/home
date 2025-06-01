import type { 
  SimpleClaudeAnalysisInput,
  SimpleClaudeAnalysisOutput,
  SimpleClaudeAnalysisError,
  ClaudeAnalysisResult
} from '../../domain/types';
import type { Result } from '../../common/types';
import { createError, createSuccess, classifyError } from '../../common/errorHandler';
import { generateVersionAnalysisPrompt } from '../claude/simplePromptGenerator';

export const executeClaudeAnalysisCore = async (input: SimpleClaudeAnalysisInput): Promise<Result<string>> => {
  // Core層：プロンプト生成（try/catch除去）
  const prompt = generateVersionAnalysisPrompt(input.node);
  
  // Core層：Claude解析実行
  const analysisResult: ClaudeAnalysisResult = await input.rpcClient.sendClaudeRequest(prompt);
  
  // Core層：結果処理（明示的分岐）
  if (analysisResult.status === "success") {
    return createSuccess(analysisResult.data);
  } else {
    return createError('ANALYSIS_ERROR', analysisResult.message);
  }
};
