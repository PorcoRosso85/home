/**
 * VersionStateエンティティ
 * 
 * バージョン状態の型定義と進捗状況の管理
 */

export type CompletionStatus = 'completed' | 'in_progress' | 'not_started';

export interface VersionState {
  id: string;
  timestamp: string;
  description: string;
  progress_percentage: number;
}

/**
 * VersionStateの進捗状況詳細
 */
export interface VersionCompletion extends VersionState {
  totalLocations: number;
  completedLocations: number;
  completionStatus: CompletionStatus;
  completedUriList: string[];
  previousVersion: string | null;
  nextVersion: string | null;
}

/**
 * 進捗状況の計算
 */
export function calculateCompletionStatus(progressPercentage: number): CompletionStatus {
  if (progressPercentage >= 1.0) {
    return 'completed';
  } else if (progressPercentage > 0.0) {
    return 'in_progress';
  } else {
    return 'not_started';
  }
}

/**
 * 進捗率のパーセンテージ表示
 */
export function formatProgressPercentage(progressPercentage: number, decimals: number = 1): string {
  return `${(progressPercentage * 100).toFixed(decimals)}%`;
}

/**
 * 進捗率のバリデーション
 */
export function validateProgressPercentage(value: number): { isValid: boolean; error?: string } {
  if (typeof value !== 'number') {
    return { isValid: false, error: 'Progress percentage must be a number' };
  }
  
  if (isNaN(value)) {
    return { isValid: false, error: 'Progress percentage cannot be NaN' };
  }
  
  if (value < 0.0 || value > 1.0) {
    return { isValid: false, error: 'Progress percentage must be between 0.0 and 1.0' };
  }
  
  return { isValid: true };
}

/**
 * VersionStateの完全性チェック
 */
export function validateVersionState(versionState: VersionState): { isValid: boolean; error?: string } {
  if (!versionState.id || versionState.id.trim() === '') {
    return { isValid: false, error: 'ID is required' };
  }
  
  if (!versionState.description || versionState.description.trim() === '') {
    return { isValid: false, error: 'Description is required' };
  }
  
  if (!versionState.timestamp) {
    return { isValid: false, error: 'Timestamp is required' };
  }
  
  try {
    const date = new Date(versionState.timestamp);
    if (isNaN(date.getTime())) {
      return { isValid: false, error: 'Invalid timestamp format' };
    }
  } catch (e) {
    return { isValid: false, error: 'Invalid timestamp format' };
  }
  
  const progressValidation = validateProgressPercentage(versionState.progress_percentage);
  if (!progressValidation.isValid) {
    return progressValidation;
  }
  
  return { isValid: true };
}

/**
 * タイムスタンプのフォーマット
 */
export function formatTimestamp(timestamp: string, options?: Intl.DateTimeFormatOptions): string {
  const date = new Date(timestamp);
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  };
  
  return date.toLocaleString('ja-JP', options || defaultOptions);
}

/**
 * 進捗状況のサマリー生成
 */
export function generateProgressSummary(versions: VersionCompletion[]): {
  total: number;
  completed: number;
  inProgress: number;
  notStarted: number;
  averageProgress: number;
} {
  const total = versions.length;
  const completed = versions.filter(v => v.completionStatus === 'completed').length;
  const inProgress = versions.filter(v => v.completionStatus === 'in_progress').length;
  const notStarted = versions.filter(v => v.completionStatus === 'not_started').length;
  
  const averageProgress = total > 0
    ? versions.reduce((sum, v) => sum + v.progress_percentage, 0) / total
    : 0;
  
  return {
    total,
    completed,
    inProgress,
    notStarted,
    averageProgress,
  };
}

/**
 * バージョン間の依存関係チェック
 */
export function checkVersionDependencies(versions: VersionCompletion[]): {
  hasInconsistencies: boolean;
  inconsistencies: Array<{
    versionId: string;
    issue: string;
  }>;
} {
  const inconsistencies: Array<{ versionId: string; issue: string }> = [];
  
  // 各バージョンの状態をチェック
  for (const version of versions) {
    // 前バージョンが完了していないのに後バージョンが完了している場合
    if (version.completionStatus === 'completed' && version.previousVersion) {
      const previousVersion = versions.find(v => v.id === version.previousVersion);
      if (previousVersion && previousVersion.completionStatus !== 'completed') {
        inconsistencies.push({
          versionId: version.id,
          issue: `Previous version ${version.previousVersion} is not completed`
        });
      }
    }
    
    // 進捗率と完了状態の不整合
    if (version.progress_percentage === 1.0 && version.completionStatus !== 'completed') {
      inconsistencies.push({
        versionId: version.id,
        issue: 'Progress is 100% but status is not completed'
      });
    }
    
    if (version.progress_percentage < 1.0 && version.completionStatus === 'completed') {
      inconsistencies.push({
        versionId: version.id,
        issue: 'Status is completed but progress is less than 100%'
      });
    }
  }
  
  return {
    hasInconsistencies: inconsistencies.length > 0,
    inconsistencies
  };
}
