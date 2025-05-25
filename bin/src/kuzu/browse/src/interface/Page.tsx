/**
 * ページロジック・状態管理を担当するコンポーネント
 */
import React, { useState } from 'react';
import { VersionStates } from './presentation/VersionStates';
import type { TreeNode } from '../domain/types';
import { useVersionStates } from '../application/hooks/useVersionStates';
import { useLocationUris } from '../application/hooks/useLocationUris';
import { useDatabaseConnection } from '../infrastructure/database/useDatabaseConnection';

/**
 * バージョンとLocationURIのネストされたツリーを表示するページ
 */
export const Page: React.FC = () => {
  const { isConnected, error: connectionError, dbConnection } = useDatabaseConnection();
  
  // バージョン管理用Hook
  const { 
    versions, 
    loading: loadingVersions, 
    error: versionError 
  } = useVersionStates(dbConnection);
  
  // 選択されたバージョンのIDを状態として保持
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  
  // LocationURI取得用Hook（選択されたバージョンのみ）
  const { 
    treeData, 
    loading: loadingLocations, 
    error: locationError 
  } = useLocationUris(dbConnection, selectedVersionId);

  // バージョン選択ハンドラ
  const handleVersionClick = (versionId: string) => {
    setSelectedVersionId(versionId);
    console.log(`Version ${versionId} selected`);
  };

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

  return (
    <div>
      <VersionStates 
        versions={versions}
        selectedVersionId={selectedVersionId}
        loading={loadingVersions}
        error={versionError}
        onVersionClick={handleVersionClick}
        locationTreeData={treeData}
        locationLoading={loadingLocations}
        locationError={locationError}
      />
    </div>
  );
};
