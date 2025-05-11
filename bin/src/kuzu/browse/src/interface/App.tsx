import React, { useState, useEffect } from 'react';
import { LoadingView } from './components/LoadingView';
import { ErrorView } from './components/ErrorView';
import { TreeView } from './components/TreeView';
import { useDatabaseConnection } from '../infrastructure/database/useDatabaseConnection';
import { useVersionData } from '../application/hooks/useVersionData';
import { createVersionCompletionService } from '../application/services/VersionCompletionService';
import { createVersionProgressRepository } from '../infrastructure/repository/VersionProgressRepository';

const App = () => {
  const { dbConnection, isConnected, error: dbError } = useDatabaseConnection();
  const [progressData, setProgressData] = useState<{[key: string]: number}>({});
  
  const { 
    versions, 
    selectedVersionId, 
    setSelectedVersionId, 
    treeData, 
    loading, 
    error 
  } = useVersionData(dbConnection);

  // 進捗データサービスの初期化
  const repository = createVersionProgressRepository();
  const versionService = createVersionCompletionService(repository);

  // バージョン選択時に進捗データを取得
  useEffect(() => {
    const fetchProgressData = async () => {
      if (!dbConnection) return;
      
      try {
        const statistics = await versionService.getStatistics(dbConnection);
        const progressMap: {[key: string]: number} = {};
        statistics.versions.forEach(version => {
          progressMap[version.versionId] = version.completionRate;
        });
        setProgressData(progressMap);
      } catch (error) {
        console.error('Failed to fetch progress data:', error);
      }
    };

    if (dbConnection && isConnected) {
      fetchProgressData();
    }
  }, [dbConnection, isConnected]);

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
      {/* コンテンツエリア */}
      <div style={{ flex: 1, overflow: 'auto' }}>
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
                    {progressData[version.id] !== undefined && (
                      ` （進捗率: ${Math.round(progressData[version.id])}%）`
                    )}
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
      </div>
    </div>
  );
};

export default App;
