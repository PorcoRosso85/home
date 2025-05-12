/**
 * バージョンツリーとLocationURIツリーを表示するコンポーネント
 */
import React, { useState } from 'react';
import { TreeView } from './TreeView';
import type { TreeNode } from '../../domain/types';
import { useVersionTreeData } from '../../application/hooks/useVersionTreeData';
import { useLocationUriTree } from '../../application/hooks/useLocationUriTree';
import { useDatabaseConnection } from '../../infrastructure/database/useDatabaseConnection';

/**
 * バージョンとLocationURIのネストされたツリーを表示するコンポーネント
 */
export const VersionTreeView: React.FC = () => {
  const { isConnected, error: connectionError } = useDatabaseConnection();
  const { versionTree, loading: loadingVersions, error: versionError } = useVersionTreeData();
  // 選択されたバージョンのIDを状態として保持
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  // 選択されたバージョンのLocationURIツリーを取得
  const { locationTree, loading: loadingLocations, error: locationError } = useLocationUriTree(selectedVersionId);

  // バージョンノードがクリックされたときのハンドラ
  const handleVersionNodeClick = (node: TreeNode) => {
    if (node.nodeType === 'version') {
      setSelectedVersionId(node.id);
      console.log(`Version ${node.id} selected`);
    }
  };

  // バージョンツリーとLocationURIツリーを結合する
  const combineTreeData = (versions: TreeNode[], locations: TreeNode[], selectedId: string): TreeNode[] => {
    return versions.map(versionNode => {
      // 選択されたバージョンのノードにLocationURIツリーを追加
      if (versionNode.id === selectedId) {
        return {
          ...versionNode,
          children: locations
        };
      }
      
      // 子ノードも再帰的に処理
      if (versionNode.children && versionNode.children.length > 0) {
        return {
          ...versionNode,
          children: combineTreeData(versionNode.children, locations, selectedId)
        };
      }
      
      return versionNode;
    });
  };

  // 結合されたツリーデータ
  const combinedTreeData = selectedVersionId 
    ? combineTreeData(versionTree, locationTree, selectedVersionId)
    : versionTree;

  // データベース接続エラーの表示
  if (connectionError) {
    return (
      <div>
        <div style={{ color: 'red', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          データベース接続エラー: {connectionError.message}
        </div>
      </div>
    );
  }

  // データベース接続待機中
  if (!isConnected) {
    return <div>データベース接続を待機中...</div>;
  }

  // ロード中またはエラー状態の表示
  if (loadingVersions) {
    return <div>バージョンデータを読み込み中...</div>;
  }

  if (versionError) {
    return (
      <div>
        <div style={{ color: 'red', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          バージョンデータ読み込みエラー: {versionError}
        </div>
      </div>
    );
  }

  return (
    <div>
      <p>バージョンをクリックするとそのバージョンに関連するLocationURIが表示されます</p>
      
      {/* LocationURIエラーメッセージの表示 */}
      {locationError && (
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          LocationURI読み込みエラー: {locationError}
        </div>
      )}
      
      {/* ツリービューの表示 */}
      {versionTree.length === 0 ? (
        <p>利用可能なバージョンがありません。</p>
      ) : (
        <TreeView 
          treeData={combinedTreeData}
          onNodeClick={handleVersionNodeClick}
        />
      )}
      
      {/* 選択されたバージョンのLocationURIロード中の表示 */}
      {loadingLocations && selectedVersionId && (
        <div style={{ marginTop: '10px', padding: '5px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          LocationURIデータを読み込み中...
        </div>
      )}
    </div>
  );
};
