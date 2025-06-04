/**
 * バージョン選択・表示用コンポーネント（薄いPresentation）
 */
import React, { useState } from 'react';
import { Tree } from '../components/Tree';
import { ContextMenu } from '../components/ContextMenu';
import { ClaudeResultView } from '../components/claude/ClaudeResultView';
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
  const handleClaudeRequest = (prompt: string, node: NodeData, action?: string, sessionName?: string, useTmux?: boolean) => {
    // tmux-claude-echoアクションの場合、セッション名をstateに保存
    if (action === 'tmux-claude-echo' && sessionName) {
      setState(prev => ({ ...prev, lastAction: action, lastSessionName: sessionName }));
    }
    
    // claude-boss-testアクションの場合、2つの並列プロセスを起動
    if (action === 'claude-boss-test') {
      console.log('='.repeat(60));
      console.log('🚀 Claude親分テスト開始！2つの親分を並列起動します');
      console.log('='.repeat(60));
      
      // 親分1を起動
      const prompt1 = prompt.replace('<id>', '1');
      console.log('👑 親分1を起動:', prompt1.substring(0, 50) + '...');
      sendClaudeRequestWithPrompt(prompt1, false);
      
      // 親分2を起動（少し遅延させて別プロセスとして認識させる）
      setTimeout(() => {
        const prompt2 = prompt.replace('<id>', '2');
        console.log('👑 親分2を起動:', prompt2.substring(0, 50) + '...');
        sendClaudeRequestWithPrompt(prompt2, false);
      }, 100);
    } else {
      sendClaudeRequestWithPrompt(prompt, useTmux, sessionName);
    }
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
      <ClaudeResultView
        loading={claudeLoading}
        result={result}
        error={claudeError}
        sessionInfo={
          state.lastAction === 'tmux-claude-echo' && state.lastSessionName
            ? { action: state.lastAction, sessionName: state.lastSessionName }
            : null
        }
      />
      
      {/* 分離されたコンテキストメニューコンポーネント */}
      <ContextMenu
        contextMenu={state.contextMenu}
        onContextMenuUpdate={(menu) => setState(prev => ({ ...prev, contextMenu: menu }))}
        onMenuAction={versionStatesLogic.handleMenuAction}
      />
    </div>
  );
};
