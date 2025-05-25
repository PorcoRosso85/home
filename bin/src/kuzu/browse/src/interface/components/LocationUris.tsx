/**
 * LocationURI表示用コンポーネント
 */
import React from 'react';
import { TreeView } from './TreeView';
import type { TreeNode } from '../../domain/types';

interface LocationUrisProps {
  treeData: TreeNode[];
  loading: boolean;
  error: string | null;
  selectedVersionId: string;
}

/**
 * LocationURIツリーを表示するコンポーネント
 */
export const LocationUris: React.FC<LocationUrisProps> = ({
  treeData,
  loading,
  error,
  selectedVersionId
}) => {
  // エラーメッセージの表示
  if (error) {
    return (
      <div style={{ color: 'red', marginBottom: '10px', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
        LocationURI読み込みエラー: {error}
      </div>
    );
  }

  // ロード中の表示
  if (loading && selectedVersionId) {
    return (
      <div style={{ marginTop: '10px', padding: '5px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
        LocationURIデータを読み込み中...
      </div>
    );
  }

  // データがない場合は何も表示しない
  if (!selectedVersionId || treeData.length === 0) {
    return null;
  }

  return (
    <TreeView 
      treeData={treeData}
      onNodeClick={() => {}}
    />
  );
};
