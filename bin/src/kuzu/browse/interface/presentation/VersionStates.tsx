/**
 * バージョン選択・表示用コンポーネント（薄いPresentation）
 */
import React, { useState } from 'react';
import { Tree } from '../components/Tree';
import type { VersionState, NodeData, VersionStatesReactState } from '../../domain/types';
import { useSimpleClaudeAnalysis } from '../../application/claude/useSimpleClaudeAnalysis.ts';
import { computeVersionStatesCore } from './VersionStatesCore';

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
    contextMenu: { show: false, x: 0, y: 0, node: null }
  });
  
  const { loading: claudeLoading, result, error: claudeError, analyzeVersion } = useSimpleClaudeAnalysis();

  const versionStatesLogic = computeVersionStatesCore(
    { ...props, expandedVersions: state.expandedVersions, contextMenu: state.contextMenu },
    (newExpanded) => setState(prev => ({ ...prev, expandedVersions: newExpanded })),
    (menu) => setState(prev => ({ ...prev, contextMenu: menu })),
    (node) => analyzeVersion(node)
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
        </div>
      )}
      
      {claudeError && (
        <div style={{ padding: '10px', backgroundColor: '#ffe8e8', margin: '10px 0', border: '1px solid #f44336' }}>
          <h4>Claude解析エラー:</h4>
          <p>{claudeError}</p>
        </div>
      )}
      
      {/* 右クリックコンテキストメニュー */}
      {state.contextMenu.show && (
        <>
          <div 
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 999
            }}
            onClick={versionStatesLogic.handleCloseContextMenu}
          />
          <div
            style={{
              position: 'fixed',
              top: state.contextMenu.y,
              left: state.contextMenu.x,
              backgroundColor: 'white',
              border: '1px solid #ccc',
              borderRadius: '4px',
              boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
              zIndex: 1000,
              minWidth: '150px'
            }}
          >
            <button
              style={{
                width: '100%',
                padding: '8px 12px',
                border: 'none',
                backgroundColor: 'transparent',
                textAlign: 'left',
                cursor: 'pointer'
              }}
              onClick={versionStatesLogic.handleClaudeAnalysis}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0f0f0'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              Claude解析
            </button>
          </div>
        </>
      )}
    </div>
  );
};
