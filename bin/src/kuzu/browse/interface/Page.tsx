/**
 * ページコンポーネント（薄いContainer）
 * Core関数を使用し、React表示のみに責務を限定
 */
import React, { useState, useMemo } from 'react';
import { VersionStates } from './presentation/VersionStates';
import { useVersionStates } from '../application/hooks/useVersionStates';
import { useLocationUris } from '../application/hooks/useLocationUris';
import { useDatabaseConnection } from '../infrastructure/database/useDatabaseConnection';
import { createPageLogicCore } from './page';

export const Page: React.FC = () => {
  const pageLogic = useMemo(() => createPageLogicCore(), []);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  
  const { isConnected, error: connectionError, dbConnection } = useDatabaseConnection();
  const { versions, loading: loadingVersions, error: versionError } = useVersionStates(dbConnection);
  const { treeData, loading: loadingLocations, error: locationError } = useLocationUris(dbConnection, selectedVersionId);

  const pageState = pageLogic.computePageState({
    dbConnection,
    isConnected,
    connectionError,
    versions,
    loadingVersions,
    versionError,
    treeData,
    loadingLocations,
    locationError
  });

  const handleVersionClick = (versionId: string) => {
    pageLogic.updateSelectedVersion(versionId);
    setSelectedVersionId(versionId);
  };

  if (pageState.shouldShowConnectionError) {
    return (
      <div>
        <div style={{ color: 'red', padding: '10px', border: '1px solid #f00', borderRadius: '4px' }}>
          データベース接続エラー: {pageState.connectionErrorMessage}
        </div>
      </div>
    );
  }

  if (pageState.shouldShowConnectionWaiting) {
    return <div>データベース接続を待機中...</div>;
  }

  if (pageState.shouldShowMainContent) {
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
  }

  return null;
};
