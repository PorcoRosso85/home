/**
 * バージョン進捗状況管理サービス
 * 
 * LocationURIの完了状態とVersionStateの進捗率を管理する
 */

import type { LocationUriEntity } from '../../domain/entities/locationUri';
import type { VersionStateEntity, CompletionStatus } from '../../domain/entities/versionState';
import type { QueryResult } from '../../domain/entities/queryResult';
import { createQueryRepository } from '../../infrastructure/factories/repositoryFactory';

/**
 * LocationURIの完了状態を設定
 */
export async function markLocationUriCompleted(
  connection: any,
  uriId: string,
  completed: boolean
): Promise<void> {
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'mark_locationuri_completed', {
    uri_id: uriId,
    completed: completed
  });
  
  if (!result.success) {
    throw new Error(`Failed to mark LocationURI ${uriId} as ${completed ? 'completed' : 'incomplete'}: ${result.error}`);
  }
}

/**
 * 複数LocationURIの完了状態を一括更新
 */
export async function batchUpdateLocationUriCompletion(
  connection: any,
  updates: Array<{ uriId: string; completed: boolean }>
): Promise<void> {
  const uriIds = updates.map(u => u.uriId);
  const completedValues = updates.map(u => u.completed);
  
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'batch_update_locationuri_completion', {
    uri_ids: uriIds,
    completed_values: completedValues
  });
  
  if (!result.success) {
    throw new Error(`Failed to batch update LocationURI completion: ${result.error}`);
  }
}

/**
 * 指定バージョンの進捗率を自動計算・更新
 */
export async function calculateVersionProgress(
  connection: any,
  versionId: string
): Promise<{
  versionId: string;
  totalLocations: number;
  completedLocations: number;
  progressPercentage: number;
}> {
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'calculate_version_progress', {
    version_id: versionId
  });
  
  if (!result.success || !result.data || result.data.length === 0) {
    throw new Error(`Failed to calculate progress for version ${versionId}: ${result.error}`);
  }
  
  const data = result.data[0];
  return {
    versionId: data.version_id,
    totalLocations: data.total_locations,
    completedLocations: data.completed_locations,
    progressPercentage: data.progress_percentage
  };
}

/**
 * バージョンの進捗率を直接更新
 */
export async function updateVersionProgress(
  connection: any,
  versionId: string,
  progressPercentage: number
): Promise<void> {
  // 進捗率を0.0から1.0の範囲に正規化
  const normalizedProgress = Math.max(0.0, Math.min(1.0, progressPercentage));
  
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'update_version_progress', {
    version_id: versionId,
    progress_percentage: normalizedProgress
  });
  
  if (!result.success) {
    throw new Error(`Failed to update progress for version ${versionId}: ${result.error}`);
  }
}

/**
 * 全バージョンの完了状況サマリーを取得
 */
export async function getCompletionProgressSummary(connection: any): Promise<Array<{
  versionId: string;
  timestamp: string;
  description: string;
  progressPercentage: number;
  totalLocations: number;
  completedLocations: number;
  completionStatus: CompletionStatus;
}>> {
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'get_completion_progress_summary', {});
  
  if (!result.success || !result.data) {
    throw new Error(`Failed to get completion progress summary: ${result.error}`);
  }
  
  return result.data.map((item: any) => ({
    versionId: item.version_id,
    timestamp: item.timestamp,
    description: item.description,
    progressPercentage: item.progress_percentage,
    totalLocations: item.total_locations,
    completedLocations: item.completed_locations,
    completionStatus: item.completion_status
  }));
}

/**
 * 指定バージョンの完了状況詳細を取得
 */
export async function getVersionCompletionStatus(
  connection: any,
  versionId?: string
): Promise<Array<{
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
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'get_version_completion_status', 
    versionId ? { version_id: versionId } : {});
  
  if (!result.success || !result.data) {
    throw new Error(`Failed to get version completion status: ${result.error}`);
  }
  
  return result.data.map((item: any) => ({
    versionId: item.version_id,
    timestamp: item.timestamp,
    description: item.description,
    progressPercentage: item.progress_percentage,
    totalLocations: item.total_locations,
    completedLocations: item.completed_locations,
    completedUriList: item.completed_uri_list || [],
    previousVersion: item.previous_version,
    nextVersion: item.next_version
  }));
}

/**
 * 指定バージョンの未完了LocationURI一覧を取得
 */
export async function getIncompleteLocationUris(
  connection: any,
  versionId: string
): Promise<Array<LocationUriEntity>> {
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'get_incomplete_locationuris_by_version', {
    version_id: versionId
  });
  
  if (!result.success || !result.data) {
    throw new Error(`Failed to get incomplete LocationURIs for version ${versionId}: ${result.error}`);
  }
  
  return result.data.map((item: any) => ({
    uri_id: item.uri_id,
    scheme: item.scheme,
    authority: item.authority,
    path: item.path,
    fragment: item.fragment,
    query: item.query,
    completed: item.is_completed
  }));
}

/**
 * 完了/未完了の統計情報を取得
 */
export async function getCompletionStatistics(connection: any): Promise<{
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
  const repository = await createQueryRepository();
  const result = await repository.executeQuery(connection, 'get_completion_statistics', {});
  
  if (!result.success || !result.data || result.data.length === 0) {
    throw new Error(`Failed to get completion statistics: ${result.error}`);
  }
  
  const statistics = result.data[0].statistics;
  return {
    totalVersions: statistics.total_versions,
    overallTotalLocations: statistics.overall_total_locations,
    overallCompletedLocations: statistics.overall_completed_locations,
    overallIncompleteLocations: statistics.overall_incomplete_locations,
    completionStatusCounts: statistics.completion_status_counts,
    versionDetails: statistics.version_details
  };
}

/**
 * バージョンと関連LocationURIを一括処理
 * LocationURIの状態変更後、自動的にバージョンの進捗率を再計算する
 */
export async function processVersionProgress(
  connection: any,
  versionId: string,
  locationUriUpdates: Array<{ uriId: string; completed: boolean }>
): Promise<{
  versionId: string;
  updatedLocations: number;
  totalLocations: number;
  completedLocations: number;
  progressPercentage: number;
}> {
  try {
    // 1. LocationURIの状態を一括更新
    await batchUpdateLocationUriCompletion(connection, locationUriUpdates);
    
    // 2. バージョンの進捗率を自動計算・更新
    const progressResult = await calculateVersionProgress(connection, versionId);
    
    return {
      versionId: progressResult.versionId,
      updatedLocations: locationUriUpdates.length,
      totalLocations: progressResult.totalLocations,
      completedLocations: progressResult.completedLocations,
      progressPercentage: progressResult.progressPercentage
    };
  } catch (error) {
    throw new Error(`Failed to process version progress for ${versionId}: ${error}`);
  }
}

/**
 * 全バージョンの進捗率を一括再計算
 */
export async function recalculateAllVersionProgress(connection: any): Promise<Array<{
  versionId: string;
  previousProgress: number;
  newProgress: number;
  totalLocations: number;
  completedLocations: number;
}>> {
  // 1. 全バージョンを取得
  const repository = await createQueryRepository();
  const versionsResult = await repository.executeQuery(connection, 'get_all_versions', {});
  
  if (!versionsResult.success || !versionsResult.data) {
    throw new Error(`Failed to get all versions: ${versionsResult.error}`);
  }
  
  const results = [];
  
  // 2. 各バージョンの進捗率を再計算
  for (const version of versionsResult.data) {
    const previousProgress = version.progress_percentage || 0.0;
    const progressResult = await calculateVersionProgress(connection, version.id);
    
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
