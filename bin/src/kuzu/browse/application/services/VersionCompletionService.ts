/**
 * バージョン進捗状況管理のビジネスロジック
 * 
 * UIコンポーネントとKuzuDBの間の中間層として機能
 */

import type { LocationUriEntity } from '../../../query/domain/entities/locationUri';
import type { VersionStateEntity, CompletionStatus } from '../../../../query/domain/entities/versionState';
import type { VersionProgressRepository } from '../../infrastructure/repository/VersionProgressRepository';

export type VersionCompletion = {
  versionId: string;
  timestamp: string;
  description: string;
  progressPercentage: number;
  totalLocations: number;
  completedLocations: number;
  completionStatus: CompletionStatus;
  previousVersion: string | null;
  nextVersion: string | null;
  completedUriList: string[];
}

export type StatisticsData = {
  totalVersions: number;
  overallTotalLocations: number;
  overallCompletedLocations: number;
  overallIncompleteLocations: number;
  completionStatusCounts: {
    completed: number;
    in_progress: number;
    not_started: number;
  };
  versionDetails: Array<{
    versionId: string;
    total: number;
    completed: number;
    incomplete: number;
    progress: number;
  }>;
}

export function createVersionCompletionService(repository: VersionProgressRepository) {
  /**
   * 指定バージョンの進捗率を計算・更新
   */
  async function calculateAndUpdateVersionProgress(
    dbConnection: any,
    versionId: string
  ): Promise<VersionCompletion> {
    const result = await repository.calculateVersionProgress(dbConnection, versionId);
    
    // 計算結果から最新の状態を取得
    const [completion] = await repository.getVersionCompletionStatus(dbConnection, versionId);
    return completion;
  }

  /**
   * バージョンの進捗率を直接設定
   */
  async function setVersionProgress(
    dbConnection: any,
    versionId: string,
    progressPercentage: number
  ): Promise<void> {
    // 0.0から1.0の範囲に正規化
    const normalizedProgress = Math.max(0.0, Math.min(1.0, progressPercentage));
    await repository.updateVersionProgress(dbConnection, versionId, normalizedProgress);
  }

  /**
   * 全バージョンの進捗状況を取得
   */
  async function getCompletionSummary(dbConnection: any): Promise<VersionCompletion[]> {
    const summary = await repository.getCompletionProgressSummary(dbConnection);
    return summary.map(item => ({
      ...item,
      completedUriList: [],
      previousVersion: null,
      nextVersion: null
    }));
  }

  /**
   * 指定バージョンの詳細進捗情報を取得
   */
  async function getVersionCompletionDetails(
    dbConnection: any,
    versionId: string
  ): Promise<VersionCompletion> {
    const [completion] = await repository.getVersionCompletionStatus(dbConnection, versionId);
    return completion;
  }

  /**
   * 指定バージョンのLocationURI一覧を取得
   */
  async function getIncompleteLocationUris(
    dbConnection: any,
    versionId: string
  ): Promise<LocationUriEntity[]> {
    const result = await repository.getLocationUrisByVersion(dbConnection, versionId);
    
    // エラーの場合は空配列を返す
    if ('code' in result) {
      logger.error(`Failed to get LocationURIs for version ${versionId}:`, result.message);
      return [];
    }
    
    return result;
  }

  /**
   * 全体の統計情報を取得
   */
  async function getStatistics(dbConnection: any): Promise<StatisticsData> {
    return await repository.getCompletionStatistics(dbConnection);
  }

  /**
   * 全バージョンの進捗率を再計算
   */
  async function recalculateAllProgress(dbConnection: any): Promise<Array<{
    versionId: string;
    previousProgress: number;
    newProgress: number;
    totalLocations: number;
    completedLocations: number;
    progressChange: number;
  }>> {
    const results = await repository.recalculateAllVersionProgress(dbConnection);
    
    return results.map(result => ({
      ...result,
      progressChange: result.newProgress - result.previousProgress
    }));
  }

  /**
   * バージョン間の進捗比較分析
   */
  async function analyzeVersionProgress(dbConnection: any): Promise<{
    completedVersions: VersionCompletion[];
    inProgressVersions: VersionCompletion[];
    notStartedVersions: VersionCompletion[];
    averageProgress: number;
    totalProgress: number;
    nextMilestone: VersionCompletion | null;
  }> {
    const allVersions = await getCompletionSummary(dbConnection);
    
    const completedVersions = allVersions.filter(v => v.progressPercentage >= 1.0);
    const inProgressVersions = allVersions.filter(v => v.progressPercentage > 0 && v.progressPercentage < 1.0);
    const notStartedVersions = allVersions.filter(v => v.progressPercentage === 0);
    
    const averageProgress = allVersions.length > 0
      ? allVersions.reduce((sum, v) => sum + v.progressPercentage, 0) / allVersions.length
      : 0;
    
    const totalProgress = allVersions.length > 0
      ? completedVersions.length / allVersions.length
      : 0;
    
    // 最も進捗率が高い未完了バージョンを次のマイルストーンとして特定
    const nextMilestone = inProgressVersions
      .sort((a, b) => b.progressPercentage - a.progressPercentage)[0] || null;
    
    return {
      completedVersions,
      inProgressVersions,
      notStartedVersions,
      averageProgress,
      totalProgress,
      nextMilestone
    };
  }

  /**
   * 進捗レポートの生成
   */
  async function generateProgressReport(dbConnection: any): Promise<{
    summary: {
      overallProgress: number;
      completedVersions: number;
      totalVersions: number;
      completedLocations: number;
      totalLocations: number;
    };
    detailedVersions: VersionCompletion[];
    recommendations: string[];
    statistics: StatisticsData;
  }> {
    const [allVersions, statistics] = await Promise.all([
      getCompletionSummary(dbConnection),
      getStatistics(dbConnection)
    ]);
    
    const recommendations: string[] = [];
    
    // 未完了が多いバージョンを特定
    const highIncompleteVersions = allVersions
      .filter(v => (v.totalLocations - v.completedLocations) > 5)
      .sort((a, b) => (b.totalLocations - b.completedLocations) - (a.totalLocations - a.completedLocations))
      .slice(0, 3);
    
    if (highIncompleteVersions.length > 0) {
      recommendations.push(`${highIncompleteVersions[0].versionId} に未完了項目が多く残っています`);
    }
    
    // 進捗が停滞しているバージョンを特定
    const stagnantVersions = allVersions.filter(v => 
      v.progressPercentage > 0 && v.progressPercentage < 0.3
    );
    
    if (stagnantVersions.length > 0) {
      recommendations.push('進捗が停滞しているバージョンがあります。優先度を見直してください');
    }
    
    // 完了が近いバージョンを特定
    const nearCompleteVersions = allVersions.filter(v => 
      v.progressPercentage >= 0.8 && v.progressPercentage < 1.0
    );
    
    if (nearCompleteVersions.length > 0) {
      recommendations.push(`${nearCompleteVersions.length}個のバージョンが完了間近です`);
    }
    
    return {
      summary: {
        overallProgress: statistics.overallTotalLocations > 0
          ? statistics.overallCompletedLocations / statistics.overallTotalLocations
          : 0,
        completedVersions: statistics.completionStatusCounts.completed,
        totalVersions: statistics.totalVersions,
        completedLocations: statistics.overallCompletedLocations,
        totalLocations: statistics.overallTotalLocations
      },
      detailedVersions: allVersions,
      recommendations,
      statistics
    };
  }

  return {
    calculateAndUpdateVersionProgress,
    setVersionProgress,
    getCompletionSummary,
    getVersionCompletionDetails,
    getIncompleteLocationUris,
    getStatistics,
    recalculateAllProgress,
    analyzeVersionProgress,
    generateProgressReport
  };
}

export type VersionCompletionServiceType = ReturnType<typeof createVersionCompletionService>;
