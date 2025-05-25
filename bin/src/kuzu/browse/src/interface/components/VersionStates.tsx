/**
 * バージョン選択・表示用コンポーネント
 */
import React from 'react';
import { TreeView } from './TreeView';
import type { TreeNode, VersionState } from '../../domain/types';

interface VersionStatesProps {
  versions: VersionState[];
  selectedVersionId: string;
  loading: boolean;
  error: string | null;
  onVersionClick: (versionId: string) => void;
}

/**
 * バージョン一覧をツリー形式で表示するコンポーネント
 */
export const VersionStates: React.FC<VersionStatesProps> = ({
  versions,
  selectedVersionId,
  loading,
  error,
  onVersionClick
}) => {
  // バージョン一覧をツリー形式に変換
  const versionTree: TreeNode[] = versions.map(version => ({
    id: version.id,
    name: `${version.id} - ${version.description}`,
    nodeType: 'version',
    children: [],
    from_version: version.id,
    isCurrentVersion: version.id === selectedVersionId
  }));

  // バージョンノードがクリックされたときのハンドラ
  const handleVersionNodeClick = (node: TreeNode) => {
    if (node.nodeType === 'version') {
      onVersionClick(node.id);
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

  return (
    <TreeView 
      treeData={versionTree}
      onNodeClick={handleVersionNodeClick}
    />
  );
};
