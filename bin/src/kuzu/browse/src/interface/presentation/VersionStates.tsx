/**
 * バージョン選択・表示用コンポーネント
 */
import React, { useState } from 'react';
import { Tree } from '../components/Tree';
import type { NodeData, VersionState } from '../../domain/types';

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
  const handleVersionNodeClick = (node: NodeData) => {
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
    </div>
  );
};
