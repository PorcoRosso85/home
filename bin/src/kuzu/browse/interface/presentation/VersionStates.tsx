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
import * as logger from '../../../common/infrastructure/logger.ts';
import { sendRpcCommandCore } from '../../application/hooks/claudeRequestCore';
import { env } from '../../infrastructure/config/variables';
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
  const [state, setState] = useState<VersionStatesReactState>({
    expandedVersions: new Set(),
    contextMenu: createContextMenuState()
  });
  
  const { loading: claudeLoading, result, error: claudeError, sendClaudeRequestWithPrompt } = useSimpleClaudeAnalysis();

  // 共通のClaude リクエスト処理
  const handleClaudeRequest = (prompt: string, node: NodeData, action?: string) => {
    // connection-checkの場合、RPCコマンド直接実行
    if (action === 'connection-check') {
      sendRpcCommandCore("echo", ["RPC connection OK"], {
        endpoint: env.CLAUDE_WS_ENDPOINT,
        timeout: 5000
      }).then(result => {
        if (result.success) {
          logger.info('RPC接続確認成功', { data: result.data });
          // 結果を表示（ClaudeResultViewを流用）
          sendClaudeRequestWithPrompt(`RPC接続確認成功: ${result.data}`);
        } else {
          logger.error('RPC接続確認失敗', { message: result.message });
          sendClaudeRequestWithPrompt(`RPC接続確認失敗: ${result.message}`);
        }
      });
    }
    // claude-boss-testアクションの場合、2つの並列プロセスを起動
    else if (action === 'claude-boss-test') {
      logger.info('Claude親分テスト開始！2つの親分を並列起動します');
      
      // 親分1を起動
      const prompt1 = prompt.replace('<id>', '1');
      logger.info('親分1を起動', { promptPreview: prompt1.substring(0, 50) + '...' });
      sendClaudeRequestWithPrompt(prompt1);
      
      // 親分2を起動（並列実行）
      const prompt2 = prompt.replace('<id>', '2');
      logger.info('親分2を起動', { promptPreview: prompt2.substring(0, 50) + '...' });
      sendClaudeRequestWithPrompt(prompt2);
    } else {
      sendClaudeRequestWithPrompt(prompt);
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
