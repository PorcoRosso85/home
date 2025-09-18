import { useState } from 'react';
import type { SimpleClaudeAnalysisState } from '../../domain/types';
import { sendClaudeRequestCore } from './claudeRequestCore';
import { env } from '../../infrastructure/config/variables';

export const useSimpleClaudeAnalysis = () => {
  const [state, setState] = useState<SimpleClaudeAnalysisState>({
    loading: false,
    result: null,
    error: null
  });
  
  const rpcConfig = {
    endpoint: env.CLAUDE_WS_ENDPOINT,
    timeout: 60000
  };
  
  const sendClaudeRequestWithPrompt = async (prompt: string): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null, result: null }));
    
    // Core関数を使用（責務分離）
    const result = await sendClaudeRequestCore({ 
      prompt, 
      rpcConfig
    });
    
    if (result.success) {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        result: result.data, 
        error: null 
      }));
    } else {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        result: null, 
        error: result.message 
      }));
    }
  };
  
  return { ...state, sendClaudeRequestWithPrompt };
};
