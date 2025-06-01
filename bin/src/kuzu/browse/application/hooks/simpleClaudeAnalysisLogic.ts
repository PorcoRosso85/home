import type { 
  SimpleClaudeAnalysisInput,
  SimpleClaudeAnalysisOutput,
  SimpleClaudeAnalysisError,
  ClaudeAnalysisResult
} from '../../domain/types';
import { generateVersionAnalysisPrompt } from '../claude/simplePromptGenerator';

export const executeClaudeAnalysisCore = async (input: SimpleClaudeAnalysisInput): Promise<SimpleClaudeAnalysisOutput> => {
  try {
    const prompt = generateVersionAnalysisPrompt(input.node);
    const analysisResult: ClaudeAnalysisResult = await input.rpcClient.sendClaudeRequest(prompt);
    
    if (analysisResult.status === "success") {
      return { success: true, data: analysisResult.data };
    } else {
      return {
        success: false,
        error: {
          type: 'ANALYSIS_ERROR',
          message: analysisResult.message,
          originalError: null
        }
      };
    }
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    let errorType: SimpleClaudeAnalysisError['type'] = 'UNKNOWN_ERROR';
    
    if (errorMessage.includes('rpc')) errorType = 'RPC_ERROR';
    else if (errorMessage.includes('prompt')) errorType = 'PROMPT_ERROR';
    else if (errorMessage.includes('analysis')) errorType = 'ANALYSIS_ERROR';
    
    return {
      success: false,
      error: {
        type: errorType,
        message: `Claude解析でエラーが発生しました: ${errorMessage}`,
        originalError: error
      }
    };
  }
};
