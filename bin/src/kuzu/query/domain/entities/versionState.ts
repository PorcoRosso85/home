/**
 * VersionStateエンティティ
 * 
 * KuzuDBのVersionStateノードを表現する型定義と関連関数
 */

/**
 * VersionStateの基本構造
 */
export type VersionStateEntity = {
  id: string;          // バージョン識別子（主キー）
  timestamp: string;   // タイムスタンプ（ISO形式）
  description: string; // バージョンの説明
};

/**
 * VersionStateエンティティを作成する
 */
export function createVersionState(
  id: string,
  description: string,
  timestamp?: string
): VersionStateEntity {
  return {
    id,
    timestamp: timestamp || new Date().toISOString(),
    description,
  };
}

/**
 * VersionStateエンティティの複製を作成する
 */
export function cloneVersionState(versionState: VersionStateEntity): VersionStateEntity {
  return {
    id: versionState.id,
    timestamp: versionState.timestamp,
    description: versionState.description,
  };
}

/**
 * VersionStateエンティティの部分更新
 */
export function updateVersionState(
  versionState: VersionStateEntity,
  updates: Partial<Omit<VersionStateEntity, 'id'>>
): VersionStateEntity {
  return {
    ...versionState,
    ...updates,
  };
}

/**
 * タイムスタンプをDateオブジェクトに変換する
 */
export function getTimestampAsDate(versionState: VersionStateEntity): Date {
  return new Date(versionState.timestamp);
}

/**
 * 現在時刻でタイムスタンプを更新する
 */
export function updateTimestampToNow(versionState: VersionStateEntity): VersionStateEntity {
  return updateVersionState(versionState, {
    timestamp: new Date().toISOString(),
  });
}

/**
 * VersionStateエンティティの等価性チェック
 */
export function equalsVersionState(version1: VersionStateEntity, version2: VersionStateEntity): boolean {
  return (
    version1.id === version2.id &&
    version1.timestamp === version2.timestamp &&
    version1.description === version2.description
  );
}

/**
 * VersionStateエンティティをクエリパラメータに変換する
 */
export function toQueryParams(versionState: VersionStateEntity): Record<string, string> {
  return {
    id: versionState.id,
    timestamp: versionState.timestamp,
    description: versionState.description,
  };
}

/**
 * VersionStateエンティティのバリデーション
 */
export function validateVersionState(versionState: VersionStateEntity): { isValid: boolean; error?: string } {
  if (!versionState.id || versionState.id.trim() === '') {
    return { isValid: false, error: 'ID is required' };
  }
  
  if (!versionState.description || versionState.description.trim() === '') {
    return { isValid: false, error: 'Description is required' };
  }
  
  try {
    const date = new Date(versionState.timestamp);
    if (isNaN(date.getTime())) {
      return { isValid: false, error: 'Invalid timestamp format' };
    }
  } catch (e) {
    return { isValid: false, error: 'Invalid timestamp format' };
  }
  
  return { isValid: true };
}

/**
 * VersionStateエンティティのリストをタイムスタンプでソートする
 */
export function sortVersionStates(
  versions: VersionStateEntity[], 
  order: 'asc' | 'desc' = 'desc'
): VersionStateEntity[] {
  return [...versions].sort((a, b) => {
    const dateA = new Date(a.timestamp).getTime();
    const dateB = new Date(b.timestamp).getTime();
    return order === 'asc' ? dateA - dateB : dateB - dateA;
  });
}

/**
 * 指定期間内のVersionStateエンティティをフィルタリングする
 */
export function filterVersionsByDateRange(
  versions: VersionStateEntity[],
  startDate: Date,
  endDate: Date
): VersionStateEntity[] {
  return versions.filter(version => {
    const versionDate = new Date(version.timestamp);
    return versionDate >= startDate && versionDate <= endDate;
  });
}
