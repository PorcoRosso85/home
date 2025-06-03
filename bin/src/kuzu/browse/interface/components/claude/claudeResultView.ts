/**
 * Claude結果表示のPure Logic（React非依存）
 */

export type ClaudeResultInput = {
  loading: boolean;
  result: string | null;
  error: string | null;
  sessionInfo?: {
    action: string;
    sessionName: string;
  } | null;
};

export type ClaudeResultOutput = {
  shouldShowLoading: boolean;
  shouldShowResult: boolean;
  shouldShowError: boolean;
  shouldShowSessionInfo: boolean;
  loadingMessage: string;
  errorMessage: string;
  resultContent: string;
  sessionCommand: string;
  sessionName: string;
};

export const computeClaudeResultCore = (input: ClaudeResultInput): ClaudeResultOutput => {
  const { loading, result, error, sessionInfo } = input;

  return {
    shouldShowLoading: loading,
    shouldShowResult: !loading && !!result,
    shouldShowError: !loading && !!error,
    shouldShowSessionInfo: !loading && !!result && !!sessionInfo && sessionInfo.action === 'tmux-claude-echo',
    loadingMessage: 'Claude解析中...',
    errorMessage: error || '',
    resultContent: result || '',
    sessionCommand: sessionInfo ? `tmux attach -t ${sessionInfo.sessionName}` : '',
    sessionName: sessionInfo?.sessionName || ''
  };
};

export type ClaudeResultStyles = {
  loadingContainer: React.CSSProperties;
  resultContainer: React.CSSProperties;
  errorContainer: React.CSSProperties;
  sessionInfoContainer: React.CSSProperties;
  codeStyle: React.CSSProperties;
  preStyle: React.CSSProperties;
};

export const getClaudeResultStyles = (): ClaudeResultStyles => ({
  loadingContainer: {
    padding: '10px',
    backgroundColor: '#f0f0f0',
    margin: '10px 0',
    borderRadius: '4px'
  },
  resultContainer: {
    padding: '10px',
    backgroundColor: '#e8f5e8',
    margin: '10px 0',
    border: '1px solid #4CAF50',
    borderRadius: '4px'
  },
  errorContainer: {
    padding: '10px',
    backgroundColor: '#ffe8e8',
    margin: '10px 0',
    border: '1px solid #f44336',
    borderRadius: '4px'
  },
  sessionInfoContainer: {
    marginTop: '10px',
    padding: '10px',
    backgroundColor: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: '4px'
  },
  codeStyle: {
    backgroundColor: '#f5f5f5',
    padding: '2px 4px',
    borderRadius: '3px',
    fontFamily: 'monospace'
  },
  preStyle: {
    whiteSpace: 'pre-wrap' as const,
    margin: '10px 0',
    fontFamily: 'monospace'
  }
});
