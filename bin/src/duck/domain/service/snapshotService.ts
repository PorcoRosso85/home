/**
 * Snapshot Service
 * スナップショット関連のビジネスロジック
 */

import type { SnapshotInfo, TableChange } from "../types.ts";

// スナップショット間の差分計算
export function calculateSnapshotDiff(
  oldSnapshot: SnapshotInfo,
  newSnapshot: SnapshotInfo
): { added: number; modified: number; deleted: number } {
  // 簡易実装：スナップショットIDの差分から推定
  const versionDiff = newSnapshot.snapshotId - oldSnapshot.snapshotId;
  
  return {
    added: versionDiff > 0 ? 1 : 0,
    modified: 0,
    deleted: 0
  };
}

// 最新スナップショットの取得
export function getLatestSnapshot(snapshots: SnapshotInfo[]): SnapshotInfo | null {
  if (snapshots.length === 0) return null;
  
  return snapshots.reduce((latest, current) => 
    current.snapshotId > latest.snapshotId ? current : latest
  );
}

// スナップショットの検証
export function validateSnapshot(snapshot: SnapshotInfo): boolean {
  return (
    snapshot.snapshotId >= 0 &&
    snapshot.timestamp.length > 0 &&
    snapshot.tableCount >= 0
  );
}

// 変更タイプの集計
export function aggregateChanges(changes: TableChange[]): {
  inserts: number;
  updates: number;
  deletes: number;
} {
  return changes.reduce(
    (acc, change) => {
      switch (change.changeType) {
        case "insert":
          acc.inserts++;
          break;
        case "update":
          acc.updates++;
          break;
        case "delete":
          acc.deletes++;
          break;
      }
      return acc;
    },
    { inserts: 0, updates: 0, deletes: 0 }
  );
}
