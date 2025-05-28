/**
 * バージョン選択・表示用コンポーネント
 */
import React, { useState } from 'react';
import { Tree } from '../components/Tree';
import type { NodeData, VersionState, NodeClickEvent } from '../../domain/types';
import { useSimpleClaudeAnalysis } from '../../application/claude/useSimpleClaudeAnalysis.ts';

interface VersionStatesProps {
  versions: VersionState[];
  selectedVersionId: string;
  loading: boolean;
  error: string | null;
  onVersionClick: (versionId: string) => void;
  // LocationURI統合用props
  locationTreeData: NodeData[];
  locationLoading: boolean;
  locationError: string | null;
}

/**
 * バージョン一覧をツリー形式で表示するコンポーネント
 */
export const VersionStates: React.FC<VersionStatesProps> = ({
  versions,
  selectedVersionId,
  loading,
  error,
  onVersionClick,
  locationTreeData,
  locationLoading,
  locationError
}) => {
  const [expandedVersions, setExpandedVersions] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{
    show: boolean;
    x: number;
    y: number;
    node: NodeData | null;
  }>({ show: false, x: 0, y: 0, node: null });
  
  // Claude解析Hook
  const { loading: claudeLoading, result, error: claudeError, analyzeVersion } = useSimpleClaudeAnalysis();
  // バージョン一覧をツリー形式に変換
  const versionTree: NodeData[] = versions.map(version => {
    const isExpanded = expandedVersions.has(version.id);
    const baseNode: NodeData = {
      id: version.id,
      name: `${version.id} - ${version.description}`,
      nodeType: 'version',
      children: [],
      from_version: version.id,
      isCurrentVersion: version.id === selectedVersionId
    };

    // 展開されたバージョンかつLocationURIデータがある場合のみ子要素を追加
    if (isExpanded && version.id === selectedVersionId && locationTreeData.length > 0) {
      baseNode.children = locationTreeData;
    }

    return baseNode;
  });

  // バージョンノードがクリックされたときのハンドラ
  const handleVersionNodeClick = (clickEvent: NodeClickEvent) => {
    // 左クリックでversionノードの場合のみ処理
    if (clickEvent.eventType === 'left' && clickEvent.node.nodeType === 'version') {
      // バージョン選択
      onVersionClick(clickEvent.node.id);
      
      // 展開状態をトグル
      const newExpanded = new Set(expandedVersions);
      if (newExpanded.has(clickEvent.node.id)) {
        newExpanded.delete(clickEvent.node.id);
      } else {
        newExpanded.add(clickEvent.node.id);
      }
      setExpandedVersions(newExpanded);
    }
    // 右クリックでClaude解析メニュー表示
    else if (clickEvent.eventType === 'right' && clickEvent.node.nodeType === 'version') {
      setContextMenu({
        show: true,
        x: clickEvent.event.clientX,
        y: clickEvent.event.clientY,
        node: clickEvent.node
      });
      clickEvent.event.preventDefault();
    }
  };
  
  // Claude解析実行
  const handleClaudeAnalysis = async () => {
    if (contextMenu.node) {
      await analyzeVersion(contextMenu.node);
      setContextMenu({ show: false, x: 0, y: 0, node: null });
    }
  };
  
  // コンテキストメニューを閉じる
  const handleCloseContextMenu = () => {
    setContextMenu({ show: false, x: 0, y: 0, node: null });
  };

  if (loading) {
    return <div>バージョンデータを読み込み中...</div>;
  }

  if (error) {
    return (
      <div style={{ color: 'red', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
        バージョンデータ読み込みエラー: {error}
      </div>
    );
  }

  if (versions.length === 0) {
    return <p>利用可能なバージョンがありません。</p>;
  }

  // LocationURIのエラーメッセージも表示
  if (locationError) {
    return (
      <div>
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          LocationURI読み込みエラー: {locationError}
        </div>
        <Tree 
          treeData={versionTree}
          onNodeClick={handleVersionNodeClick}
        />
      </div>
    );
  }

  return (
    <div>
      <Tree 
        treeData={versionTree}
        onNodeClick={handleVersionNodeClick}
      />
      {/* LocationURIロード中の表示 */}
      {locationLoading && selectedVersionId && (
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
      {contextMenu.show && (
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
            onClick={handleCloseContextMenu}
          />
          <div
            style={{
              position: 'fixed',
              top: contextMenu.y,
              left: contextMenu.x,
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
              onClick={handleClaudeAnalysis}
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
