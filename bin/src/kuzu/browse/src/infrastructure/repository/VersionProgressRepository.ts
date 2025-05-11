/**
 * バージョン進捗データ取得・更新のリポジトリ（KuzuDB直接接続版）
 * 
 * KuzuDBと直接通信してデータを取得・更新する
 */

import type { LocationURI } from '../../domain/entities/LocationURI';
import type { VersionState, CompletionStatus } from '../../domain/entities/VersionState';
import { executeDMLQuery, executeDQLQuery } from './queryExecutor';

export interface VersionProgressRepository {
  markLocationUriCompleted(dbConnection: any, uriId: string, completed: boolean): Promise<void>;
  batchUpdateLocationUriCompletion(dbConnection: any, updates: Array<{ uriId: string; completed: boolean }>): Promise<void>;
  calculateVersionProgress(dbConnection: any, versionId: string): Promise<{
    versionId: string;
    totalLocations: number;
    completedLocations: number;
    progressPercentage: number;
  }>;
  updateVersionProgress(dbConnection: any, versionId: string, progressPercentage: number): Promise<void>;
  getCompletionProgressSummary(dbConnection: any): Promise<Array<{
    versionId: string;
    timestamp: string;
    description: string;
    progressPercentage: number;
    totalLocations: number;
    completedLocations: number;
    completionStatus: CompletionStatus;
  }>>;
  getVersionCompletionStatus(dbConnection: any, versionId?: string): Promise<Array<{
    versionId: string;
    timestamp: string;
    description: string;
    progressPercentage: number;
    totalLocations: number;
    completedLocations: number;
    completedUriList: string[];
    previousVersion: string | null;
    nextVersion: string | null;
  }>>;
  getIncompleteLocationUris(dbConnection: any, versionId: string): Promise<LocationURI[]>;
  getCompletionStatistics(dbConnection: any): Promise<{
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
  }>;
  processVersionProgress(
    dbConnection: any,
    versionId: string,
    locationUriUpdates: Array<{ uriId: string; completed: boolean }>
  ): Promise<{
    versionId: string;
    updatedLocations: number;
    totalLocations: number;
    completedLocations: number;
    progressPercentage: number;
  }>;
  recalculateAllVersionProgress(dbConnection: any): Promise<Array<{
    versionId: string;
    previousProgress: number;
    newProgress: number;
    totalLocations: number;
    completedLocations: number;
  }>>;
}

/**
 * KuzuDB直接接続による実装
 */
export function createVersionProgressRepository(): VersionProgressRepository {
  
  async function markLocationUriCompleted(dbConnection: any, uriId: string, completed: boolean): Promise<void> {
    const result = await executeDMLQuery(dbConnection, 'mark_locationuri_completed', {
      uri_id: uriId,
      completed: completed
    });
    
    if (!result.success) {
      throw new Error(`Failed to mark LocationURI as completed: ${result.error}`);
    }
  }

  async function batchUpdateLocationUriCompletion(
    dbConnection: any,
    updates: Array<{ uriId: string; completed: boolean }>
  ): Promise<void> {
    const uriIds = updates.map(u => u.uriId);
    const completedValues = updates.map(u => u.completed);
    
    const result = await executeDMLQuery(dbConnection, 'batch_update_locationuri_completion', {
      uri_ids: uriIds,
      completed_values: completedValues
    });
    
    if (!result.success) {
      throw new Error(`Failed to batch update LocationURI completion: ${result.error}`);
    }
  }

  async function calculateVersionProgress(dbConnection: any, versionId: string): Promise<{
    versionId: string;
    totalLocations: number;
    completedLocations: number;
    progressPercentage: number;
  }> {
    const result = await executeDMLQuery(dbConnection, 'calculate_version_progress', {
      version_id: versionId
    });
    
    if (!result.success || !result.data || result.data.length === 0) {
      throw new Error(`Failed to calculate progress for version ${versionId}: ${result.error}`);
    }
    
    const data = result.data[0];
    return {
      versionId: data.version_id,
      totalLocations: Number(data.total_locations),
      completedLocations: Number(data.completed_locations),
      progressPercentage: Number(data.progress_percentage)
    };
  }

  async function updateVersionProgress(
    dbConnection: any,
    versionId: string,
    progressPercentage: number
  ): Promise<void> {
    const result = await executeDMLQuery(dbConnection, 'update_version_progress', {
      version_id: versionId,
      progress_percentage: progressPercentage
    });
    
    if (!result.success) {
      throw new Error(`Failed to update progress for version ${versionId}: ${result.error}`);
    }
  }

  async function getCompletionProgressSummary(dbConnection: any): Promise<Array<{
    versionId: string;
    timestamp: string;
    description: string;
    progressPercentage: number;
    totalLocations: number;
    completedLocations: number;
    completionStatus: CompletionStatus;
  }>> {
    const result = await executeDQLQuery(dbConnection, 'get_completion_progress_summary', {});
    
    if (!result.success || !result.data) {
      throw new Error(`Failed to get completion progress summary: ${result.error}`);
    }
    
    const queryResult = await result.data.getAllObjects();
    
    return queryResult.map((item: any) => ({
      versionId: item.version_id,
      timestamp: item.timestamp,
      description: item.description,
      progressPercentage: Number(item.progress_percentage),
      totalLocations: Number(item.total_locations),
      completedLocations: Number(item.completed_locations),
      completionStatus: item.completion_status
    }));
  }

  async function getVersionCompletionStatus(dbConnection: any, versionId?: string): Promise<Array<{
    versionId: string;
    timestamp: string;
    description: string;
    progressPercentage: number;
    totalLocations: number;
    completedLocations: number;
    completedUriList: string[];
    previousVersion: string | null;
    nextVersion: string | null;
  }>> {
    const result = await executeDQLQuery(dbConnection, 'get_version_completion_status', 
      versionId ? { version_id: versionId } : {});
    
    if (!result.success || !result.data) {
      throw new Error(`Failed to get version completion status: ${result.error}`);
    }
    
    const queryResult = await result.data.getAllObjects();
    
    return queryResult.map((item: any) => ({
      versionId: item.version_id,
      timestamp: item.timestamp,
      description: item.description,
      progressPercentage: Number(item.progress_percentage),
      totalLocations: Number(item.total_locations),
      completedLocations: Number(item.completed_locations),
      completedUriList: item.completed_uri_list,
      previousVersion: item.previous_version,
      nextVersion: item.next_version
    }));
  }

  async function getIncompleteLocationUris(dbConnection: any, versionId: string): Promise<LocationURI[]> {
    const result = await executeDQLQuery(dbConnection, 'get_incomplete_locationuris_by_version', {
      version_id: versionId
    });
    
    if (!result.success || !result.data) {
      throw new Error(`Failed to get incomplete LocationURIs for version ${versionId}: ${result.error}`);
    }
    
    const queryResult = await result.data.getAllObjects();
    
    return queryResult.map((item: any) => ({
      uri_id: item.uri_id,
      scheme: item.scheme,
      authority: item.authority,
      path: item.path,
      fragment: item.fragment,
      query: item.query,
      completed: item.is_completed
    }));
  }

  async function getCompletionStatistics(dbConnection: any): Promise<{
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
  }> {
    // 全体統計を取得
    const statisticsResult = await executeDQLQuery(dbConnection, 'get_completion_statistics', {});
    
    if (!statisticsResult.success || !statisticsResult.data) {
      throw new Error(`Failed to get completion statistics: ${statisticsResult.error}`);
    }
    
    const statsQuery = await statisticsResult.data.getAllObjects();
    const stats = statsQuery[0];
    
    // バージョン詳細情報を取得
    const detailsResult = await executeDQLQuery(dbConnection, 'get_version_statistics_details', {});
    
    if (!detailsResult.success || !detailsResult.data) {
      throw new Error(`Failed to get version details: ${detailsResult.error}`);
    }
    
    const detailsQuery = await detailsResult.data.getAllObjects();
    
    return {
      totalVersions: Number(stats.total_versions),
      overallTotalLocations: Number(stats.overall_total_locations),
      overallCompletedLocations: Number(stats.overall_completed_locations),
      overallIncompleteLocations: Number(stats.overall_incomplete_locations),
      completionStatusCounts: {
        completed: Number(stats.completed_count),
        in_progress: Number(stats.in_progress_count),
        not_started: Number(stats.not_started_count),
      },
      versionDetails: detailsQuery.map((detail: any) => ({
        versionId: detail.version_id,
        total: Number(detail.total),
        completed: Number(detail.completed),
        incomplete: Number(detail.incomplete),
        progress: Number(detail.progress)
      })),
    };
  }

  async function processVersionProgress(
    dbConnection: any,
    versionId: string,
    locationUriUpdates: Array<{ uriId: string; completed: boolean }>
  ): Promise<{
    versionId: string;
    updatedLocations: number;
    totalLocations: number;
    completedLocations: number;
    progressPercentage: number;
  }> {
    // LocationURIの状態を一括更新
    await batchUpdateLocationUriCompletion(dbConnection, locationUriUpdates);
    
    // バージョンの進捗率を自動計算・更新
    const progressResult = await calculateVersionProgress(dbConnection, versionId);
    
    return {
      versionId: progressResult.versionId,
      updatedLocations: locationUriUpdates.length,
      totalLocations: progressResult.totalLocations,
      completedLocations: progressResult.completedLocations,
      progressPercentage: progressResult.progressPercentage
    };
  }

  async function recalculateAllVersionProgress(dbConnection: any): Promise<Array<{
    versionId: string;
    previousProgress: number;
    newProgress: number;
    totalLocations: number;
    completedLocations: number;
  }>> {
    // 全バージョンを取得
    const versionsResult = await executeDQLQuery(dbConnection, 'get_all_versions', {});
    
    if (!versionsResult.success || !versionsResult.data) {
      throw new Error(`Failed to get all versions: ${versionsResult.error}`);
    }
    
    const versions = await versionsResult.data.getAllObjects();
    const results = [];
    
    // 各バージョンの進捗率を再計算
    for (const version of versions) {
      const previousProgress = Number(version.progress_percentage);
      const progressResult = await calculateVersionProgress(dbConnection, version.id);
      
      results.push({
        versionId: version.id,
        previousProgress,
        newProgress: progressResult.progressPercentage,
        totalLocations: progressResult.totalLocations,
        completedLocations: progressResult.completedLocations
      });
    }
    
    return results;
  }

  return {
    markLocationUriCompleted,
    batchUpdateLocationUriCompletion,
    calculateVersionProgress,
    updateVersionProgress,
    getCompletionProgressSummary,
    getVersionCompletionStatus,
    getIncompleteLocationUris,
    getCompletionStatistics,
    processVersionProgress,
    recalculateAllVersionProgress,
  };
}

/**
 * モックリポジトリ（開発用）
 */
export function createMockVersionProgressRepository(): VersionProgressRepository {
  throw new Error('Mock repository is not implemented. Use real implementation only.');
}
