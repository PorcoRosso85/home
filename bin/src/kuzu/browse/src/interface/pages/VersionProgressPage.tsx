import React, { useState, useEffect, useCallback } from 'react';
import { VersionCompletionDashboard } from '../components/VersionCompletionDashboard';
import { LocationCompletionList } from '../components/LocationCompletionList';
import { createVersionCompletionService } from '../../application/services/VersionCompletionService';
import { createVersionProgressRepository } from '../../infrastructure/repository/VersionProgressRepository';
import { useDatabaseConnection } from '../../infrastructure/database/useDatabaseConnection';
import type { VersionCompletion, StatisticsData } from '../../application/services/VersionCompletionService';
import type { LocationURI } from '../../domain/entities/LocationURI';

// サービスとリポジトリの初期化
const repository = createVersionProgressRepository();
const versionService = createVersionCompletionService(repository);

export function VersionProgressPage() {
  const { dbConnection, isConnected, error: dbError } = useDatabaseConnection();
  const [versions, setVersions] = useState<VersionCompletion[]>([]);
  const [statistics, setStatistics] = useState<StatisticsData | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [selectedVersionDetails, setSelectedVersionDetails] = useState<VersionCompletion | null>(null);
  const [locationUris, setLocationUris] = useState<LocationURI[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // データの取得
  const fetchData = useCallback(async () => {
    if (!dbConnection) return;
    
    setIsLoading(true);
    
    const [versionsData, statsData] = await Promise.all([
      versionService.getCompletionSummary(dbConnection),
      versionService.getStatistics(dbConnection)
    ]);
    
    setVersions(versionsData);
    setStatistics(statsData);
    
    // 初期選択バージョンを設定
    if (versionsData.length > 0 && !selectedVersionId) {
      setSelectedVersionId(versionsData[0].versionId);
    }
    
    setIsLoading(false);
  }, [dbConnection, selectedVersionId]);

  // 選択されたバージョンの詳細を取得
  const fetchVersionDetails = useCallback(async (versionId: string) => {
    if (!dbConnection) return;
    
    setIsLoading(true);
    
    const [details, incompleteLocations] = await Promise.all([
      versionService.getVersionCompletionDetails(dbConnection, versionId),
      versionService.getIncompleteLocationUris(dbConnection, versionId)
    ]);
    
    setSelectedVersionDetails(details);
    setLocationUris(incompleteLocations);
    
    setIsLoading(false);
  }, [dbConnection]);

  // データベース接続後の初期データロード
  useEffect(() => {
    if (isConnected && dbConnection) {
      fetchData();
    }
  }, [isConnected, dbConnection, fetchData]);

  // バージョン選択時の処理
  useEffect(() => {
    if (selectedVersionId && dbConnection) {
      fetchVersionDetails(selectedVersionId);
    }
  }, [selectedVersionId, dbConnection, fetchVersionDetails]);

  // LocationURIの完了状態を切り替える
  const handleToggleLocationCompletion = async (uriId: string, completed: boolean) => {
    if (!dbConnection) return;
    
    setIsLoading(true);
    
    await versionService.toggleLocationCompletion(dbConnection, uriId, completed);
    
    // 進捗状況の再計算
    if (selectedVersionId) {
      await versionService.calculateAndUpdateVersionProgress(dbConnection, selectedVersionId);
    }
    
    // データの再取得
    await fetchData();
    if (selectedVersionId) {
      await fetchVersionDetails(selectedVersionId);
    }
    
    setIsLoading(false);
  };

  // 一括更新処理
  const handleBatchUpdate = async (updates: Array<{ uriId: string; completed: boolean }>) => {
    if (!selectedVersionId || !dbConnection) return;
    
    setIsLoading(true);
    
    await versionService.processVersionWithLocationUpdates(
      dbConnection,
      selectedVersionId,
      updates
    );
    
    // データの再取得
    await fetchData();
    await fetchVersionDetails(selectedVersionId);
    
    setIsLoading(false);
  };

  // 全バージョンの再計算
  const handleRecalculateAll = async () => {
    if (!dbConnection) return;
    
    setIsLoading(true);
    
    await versionService.recalculateAllProgress(dbConnection);
    
    // データの再取得
    await fetchData();
    
    setIsLoading(false);
  };

  // データベース接続確認
  if (dbError) {
    throw dbError;
  }

  // データベース接続待機中
  if (!isConnected) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
            <p className="text-gray-600">データベースに接続中...</p>
          </div>
        </div>
      </div>
    );
  }

  // データロード中
  if (isLoading || !statistics) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
            <p className="text-gray-600">データを読み込み中...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="bg-white rounded-lg border p-6">
          <h1 className="text-2xl font-bold text-gray-900">バージョン進捗管理</h1>
          <p className="text-gray-600 mt-1">各バージョンの進捗状況と完了状態を管理します</p>
        </div>
        
        {/* Dashboard */}
        <VersionCompletionDashboard
          versions={versions}
          statistics={statistics}
          onVersionSelect={setSelectedVersionId}
          onRecalculateAll={handleRecalculateAll}
          selectedVersionId={selectedVersionId}
          isLoading={isLoading}
        />
        
        {/* Location List */}
        {selectedVersionId && selectedVersionDetails && (
          <LocationCompletionList
            versionId={selectedVersionId}
            locations={locationUris}
            onToggleCompletion={handleToggleLocationCompletion}
            onBatchUpdate={handleBatchUpdate}
          />
        )}
      </div>
    </div>
  );
}
