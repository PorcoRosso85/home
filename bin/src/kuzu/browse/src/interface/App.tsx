import React, { useState } from 'react';
import { LoadingView } from './components/LoadingView';
import { ErrorView } from './components/ErrorView';
import { TreeView } from './components/TreeView';
import { VersionProgressPage } from './pages/VersionProgressPage';
import { useDatabaseConnection } from '../infrastructure/database/useDatabaseConnection';
import { useVersionData } from '../application/hooks/useVersionData';

const App = () => {
  const [currentPage, setCurrentPage] = useState<'tree' | 'progress'>('tree');
  const { dbConnection, isConnected, error: dbError } = useDatabaseConnection();
  
  const { 
    versions, 
    selectedVersionId, 
    setSelectedVersionId, 
    treeData, 
    loading, 
    error 
  } = useVersionData(dbConnection);

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
      fontFamily: 'Arial, sans-serif'
    }}>
      {/* ナビゲーションバー */}
      <div style={{ 
        display: 'flex', 
        padding: '10px 20px', 
        backgroundColor: '#f5f5f5', 
        borderBottom: '1px solid #ddd' 
      }}>
        <button
          onClick={() => setCurrentPage('tree')}
          style={{
            padding: '8px 16px',
            marginRight: '10px',
            backgroundColor: currentPage === 'tree' ? '#007bff' : '#fff',
            color: currentPage === 'tree' ? '#fff' : '#000',
            border: '1px solid #ddd',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          階層ビュー
        </button>
        <button
          onClick={() => setCurrentPage('progress')}
          style={{
            padding: '8px 16px',
            backgroundColor: currentPage === 'progress' ? '#007bff' : '#fff',
            color: currentPage === 'progress' ? '#fff' : '#000',
            border: '1px solid #ddd',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          進捗管理
        </button>
      </div>

      {/* コンテンツエリア */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {currentPage === 'tree' ? (
          <div style={{ padding: '20px', height: '100%' }}>
            {/* バージョンセレクター */}
            <div style={{ marginBottom: '20px' }}>
              <label htmlFor="version-select" style={{ marginRight: '10px' }}>
                バージョン選択（指定バージョン以前の各URIの最新状態を表示）:
              </label>
              <select 
                id="version-select"
                value={selectedVersionId} 
                onChange={(e) => setSelectedVersionId(e.target.value)}
                style={{
                  padding: '5px',
                  minWidth: '200px'
                }}
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
            <div style={{ height: 'calc(100% - 60px)', overflow: 'auto' }}>
              {selectedVersionId && treeData.length > 0 ? (
                <TreeView treeData={treeData} />
              ) : (
                <div style={{ padding: '20px', color: '#666' }}>
                  {selectedVersionId ? 'データを読み込んでいます...' : 'バージョンを選択してください'}
                </div>
              )}
            </div>
          </div>
        ) : (
          <VersionProgressPage />
        )}
      </div>
    </div>
  );
};

export default App;
