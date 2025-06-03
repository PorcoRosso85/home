/**
 * Claude結果表示UI（薄いReactラッパー）
 */
import React from 'react';
import { computeClaudeResultCore, getClaudeResultStyles, type ClaudeResultInput } from './claudeResultView';

interface ClaudeResultViewProps extends ClaudeResultInput {}

export const ClaudeResultView: React.FC<ClaudeResultViewProps> = (props) => {
  const logic = computeClaudeResultCore(props);
  const styles = getClaudeResultStyles();

  if (logic.shouldShowLoading) {
    return (
      <div style={styles.loadingContainer}>
        {logic.loadingMessage}
      </div>
    );
  }

  if (logic.shouldShowError) {
    return (
      <div style={styles.errorContainer}>
        <h4>Claude解析エラー:</h4>
        <p>{logic.errorMessage}</p>
      </div>
    );
  }

  if (logic.shouldShowResult) {
    return (
      <div style={styles.resultContainer}>
        <h4>Claude解析結果:</h4>
        <pre style={styles.preStyle}>{logic.resultContent}</pre>
        
        {logic.shouldShowSessionInfo && (
          <div style={styles.sessionInfoContainer}>
            <strong>📋 tmuxセッション情報:</strong><br/>
            セッション名: <code style={styles.codeStyle}>{logic.sessionName}</code><br/>
            接続コマンド: <code style={styles.codeStyle}>{logic.sessionCommand}</code><br/>
            <small>（すべてのセッション確認: <code style={styles.codeStyle}>tmux ls</code>）</small>
          </div>
        )}
      </div>
    );
  }

  return null;
};
