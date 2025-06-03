/**
 * バージョン選択・表示用コンポーネント（薄いPresentation）
 */
import React, { useState } from 'react';
import { Tree } from '../components/Tree';
import { ContextMenu } from '../components/ContextMenu';
import type { VersionState, NodeData, VersionStatesReactState } from '../../domain/types';
import { useSimpleClaudeAnalysis } from '../../application/claude/useSimpleClaudeAnalysis.ts';
import { computeVersionStatesCore } from './versionStates';
import { createContextMenuState } from '../components/contextMenu';

interface VersionStatesProps {
  versions: VersionState[];
  selectedVersionId: string;
  loading: boolean;
  error: string | null;
  onVersionClick: (versionId: string) => void;
  locationTreeData: NodeData[];
  locationLoading: boolean;
  locationError: string | null;
}

export const VersionStates: React.FC<VersionStatesProps> = (props) => {
  const [state, setState] = useState<VersionStatesReactState & { lastAction?: string; lastSessionName?: string }>({
    expandedVersions: new Set(),
    contextMenu: createContextMenuState()
  });
  
  const { loading: claudeLoading, result, error: claudeError, sendClaudeRequestWithPrompt } = useSimpleClaudeAnalysis();

  // 共通のClaude リクエスト処理
  const handleClaudeRequest = (prompt: string, node: NodeData, action?: string, sessionName?: string) => {
    // tmux-claude-echoアクションの場合、セッション名をstateに保存
    if (action === 'tmux-claude-echo' && sessionName) {
      setState(prev => ({ ...prev, lastAction: action, lastSessionName: sessionName }));
    }
    sendClaudeRequestWithPrompt(prompt);
  };

  const versionStatesLogic = computeVersionStatesCore(
    { ...props, expandedVersions: state.expandedVersions, contextMenu: state.contextMenu },
    (newExpanded) => setState(prev => ({ ...prev, expandedVersions: newExpanded })),
    (menu) => setState(prev => ({ ...prev, contextMenu: menu })),
    handleClaudeRequest
  );

  if (versionStatesLogic.shouldShowLoading) {
    return <div>バージョンデータを読み込み中...</div>;
  }

  if (versionStatesLogic.shouldShowError) {
    return (
      <div style={{ color: 'red', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
        バージョンデータ読み込みエラー: {versionStatesLogic.errorMessage}
      </div>
    );
  }

  if (versionStatesLogic.shouldShowEmpty) {
    return <p>{versionStatesLogic.emptyMessage}</p>;
  }

  // LocationURIエラーがある場合の表示
  if (versionStatesLogic.shouldShowLocationError) {
    return (
      <div>
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          LocationURI読み込みエラー: {versionStatesLogic.locationErrorMessage}
        </div>
        <Tree 
          treeData={versionStatesLogic.versionTree}
          onNodeClick={versionStatesLogic.handleVersionNodeClick}
        />
      </div>
    );
  }

  return (
    <div>
      <Tree 
        treeData={versionStatesLogic.versionTree}
        onNodeClick={versionStatesLogic.handleVersionNodeClick}
      />
      
      {/* LocationURIロード中表示 */}
      {props.locationLoading && props.selectedVersionId && (
        <div style={{ marginTop: '10px', padding: '5px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          LocationURIデータを読み込み中...
        </div>
      )}
      
      {/* Claude解析結果表示 */}
      {claudeLoading && (
        <div style={{ padding: '10px', backgroundColor: '#f0f0f0', margin: '10px 0' }}>
          Claude解析中...
        </div>
      )}
      
      {result && (
        <div style={{ padding: '10px', backgroundColor: '#e8f5e8', margin: '10px 0', border: '1px solid #4CAF50' }}>
          <h4>Claude解析結果:</h4>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{result}</pre>
          {/* tmux-claude-echoの場合、セッション情報を表示 */}
          {state.lastAction === 'tmux-claude-echo' && state.lastSessionName && (
            <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px' }}>
              <strong>📋 tmuxセッション情報:</strong><br/>
              セッション名: <code>{state.lastSessionName}</code><br/>
              接続コマンド: <code>tmux attach -t {state.lastSessionName}</code><br/>
              <small>（すべてのセッション確認: <code>tmux ls</code>）</small>
            </div>
          )}
        </div>
      )}
      
      {claudeError && (
        <div style={{ padding: '10px', backgroundColor: '#ffe8e8', margin: '10px 0', border: '1px solid #f44336' }}>
          <h4>Claude解析エラー:</h4>
          <p>{claudeError}</p>
        </div>
      )}
      
      {/* 分離されたコンテキストメニューコンポーネント */}
      <ContextMenu
        contextMenu={state.contextMenu}
        onContextMenuUpdate={(menu) => setState(prev => ({ ...prev, contextMenu: menu }))}
        onMenuAction={versionStatesLogic.handleMenuAction}
      />
    </div>
  );
};
