/**
 * バージョン選択・表示用コンポーネント
 */
import React, { useState } from 'react';
import { TreeView } from '../components/Tree';
import type { TreeNode, VersionState } from '../../domain/types';

interface VersionStatesProps {
  versions: VersionState[];
  selectedVersionId: string;
  loading: boolean;
  error: string | null;
  onVersionClick: (versionId: string) => void;
  onRightClick: (e: React.MouseEvent) => void;
  // LocationURI統合用props
  locationTreeData: TreeNode[];
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
  onRightClick,
  locationTreeData,
  locationLoading,
  locationError
}) => {
  const [expandedVersions, setExpandedVersions] = useState<Set<string>>(new Set());
  // バージョン一覧をツリー形式に変換
  const versionTree: TreeNode[] = versions.map(version => {
    const isExpanded = expandedVersions.has(version.id);
    const baseNode: TreeNode = {
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
  const handleVersionNodeClick = (node: TreeNode) => {
    if (node.nodeType === 'version') {
      // バージョン選択
      onVersionClick(node.id);
      
      // 展開状態をトグル
      const newExpanded = new Set(expandedVersions);
      if (newExpanded.has(node.id)) {
        newExpanded.delete(node.id);
      } else {
        newExpanded.add(node.id);
      }
      setExpandedVersions(newExpanded);
    }
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
      <div onContextMenu={onRightClick}>
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          LocationURI読み込みエラー: {locationError}
        </div>
        <TreeView 
          treeData={versionTree}
          onNodeClick={handleVersionNodeClick}
          selectedVersionId={selectedVersionId}
          onRightClick={onRightClick}
        />
      </div>
    );
  }

  return (
    <div onContextMenu={onRightClick}>
      <TreeView 
        treeData={versionTree}
        onNodeClick={handleVersionNodeClick}
        selectedVersionId={selectedVersionId}
        onRightClick={onRightClick}
      />
      {/* LocationURIロード中の表示 */}
      {locationLoading && selectedVersionId && (
        <div style={{ marginTop: '10px', padding: '5px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          LocationURIデータを読み込み中...
        </div>
      )}
    </div>
  );
};
