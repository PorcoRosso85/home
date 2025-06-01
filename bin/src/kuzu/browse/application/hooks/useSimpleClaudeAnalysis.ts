import { useState } from 'react';
import type { NodeData, SimpleClaudeAnalysisState } from '../../domain/types';
import { executeClaudeAnalysisCore } from './simpleClaudeAnalysisLogic';
import { createBasicRpcClient } from '../../infrastructure/rpc/basicRpcClient';
import { env } from '../../infrastructure/config/variables';
import { isErrorResult } from '../../common/typeGuards';

export const useSimpleClaudeAnalysis = () => {
  const [state, setState] = useState<SimpleClaudeAnalysisState>({
    loading: false,
    result: null,
    error: null
  });
  
  const rpcClient = createBasicRpcClient({
    endpoint: env.CLAUDE_WS_ENDPOINT,
    timeout: 60000
  });
  
  const analyzeVersion = async (node: NodeData): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null, result: null }));
    
    const result = await executeClaudeAnalysisCore({ node, rpcClient });
    
    if (isErrorResult(result)) {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        result: null, 
        error: result.message 
      }));
    } else {
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        result: result.data, 
        error: null 
      }));
    }
  };
  
  return { ...state, analyzeVersion };
};
