import React, { useState } from 'react';
import { LoadingView } from './components/LoadingView';
import { ErrorView } from './components/ErrorView';
import { TreeView } from './components/TreeView';
import { useDatabaseConnection } from '../infrastructure/database/useDatabaseConnection';
import { useVersionData } from '../application/hooks/useVersionData';

const App = () => {
  const { dbConnection, isConnected, error: dbError } = useDatabaseConnection();
  const [showLatestOnly, setShowLatestOnly] = useState(false); // デフォルトはバージョン指定表示
  
  const { 
    versions, 
    selectedVersionId, 
    setSelectedVersionId, 
    treeData, 
    loading, 
    error 
  } = useVersionData(dbConnection, showLatestOnly);

  if (!isConnected || loading) {
    return <LoadingView />;
  }

  if (dbError || error) {
    return <ErrorView error={dbError || error} />;
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100vh', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      {/* 表示モード切り替え */}
      <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            type="checkbox"
            checked={showLatestOnly}
            onChange={(e) => setShowLatestOnly(e.target.checked)}
          />
          全期間での最新バージョンのみ表示
        </label>
      </div>
      
      {/* バージョンセレクター */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="version-select" style={{ marginRight: '10px' }}>
          {showLatestOnly ? '(表示専用)最新バージョン:' : '指定バージョン以前の状態を表示:'}
        </label>
        <select 
          id="version-select"
          value={selectedVersionId} 
          onChange={(e) => setSelectedVersionId(e.target.value)}
          style={{
            padding: '5px',
            minWidth: '200px'
          }}
          disabled={showLatestOnly}
        >
          {versions.length === 0 ? (
            <option value="">バージョンが見つかりません</option>
          ) : (
            versions.map(version => (
              <option key={version.id} value={version.id}>
                {version.id} - {version.description}
              </option>
            ))
          )}
        </select>
      </div>
      
      {/* ツリービュー */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {selectedVersionId && treeData.length > 0 ? (
          <TreeView treeData={treeData} />
        ) : (
          <div style={{ padding: '20px', color: '#666' }}>
            {selectedVersionId ? 'データを読み込んでいます...' : 'バージョンを選択してください'}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
