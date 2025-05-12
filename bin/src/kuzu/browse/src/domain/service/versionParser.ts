/**
 * バージョン文字列のパースと処理のためのユーティリティ関数
 * 
 * TODO: SemVerに準拠したバージョン解析・比較を実装
 * TODO: プレフィックス'v'はUIレンダリング用にのみ使用し、内部処理では無視
 */

import type { VersionState } from '../types';

/**
 * パース済みバージョン情報
 */
interface ParsedVersion {
  segments: number[];  // バージョンセグメント (例: [1, 2, 3] for 1.2.3)
  displayValue: string; // 表示用文字列 (プレフィックス'v'付き)
  rawValue: string;    // 生の値 (プレフィックス'v'なし)
  original: string;    // 元の入力文字列
}

/**
 * バージョン文字列をパースする
 * プレフィックス'v'は内部処理では無視し、表示用にのみ保持する
 */
export function parseVersionString(version: string): ParsedVersion {
  // プレフィックス'v'があれば削除（内部処理用）
  const rawValue = version.startsWith('v') ? version.substring(1) : version;
  
  // セグメントに分割して数値化
  const segments = rawValue.split('.').map(segment => parseInt(segment, 10));
  
  // 表示用の値を生成（常に'v'プレフィックス付き）
  const displayValue = rawValue.startsWith('v') ? version : `v${version}`;
  
  return {
    segments,
    displayValue,
    rawValue,
    original: version
  };
}

/**
 * 2つのバージョンを比較する
 * 戻り値: 
 *   負数: v1 < v2
 *   0: v1 == v2
 *   正数: v1 > v2
 */
export function compareVersions(v1: string, v2: string): number {
  const parsed1 = parseVersionString(v1);
  const parsed2 = parseVersionString(v2);
  
  const maxLength = Math.max(parsed1.segments.length, parsed2.segments.length);
  
  for (let i = 0; i < maxLength; i++) {
    // 存在しないセグメントは0として扱う
    const segment1 = i < parsed1.segments.length ? parsed1.segments[i] : 0;
    const segment2 = i < parsed2.segments.length ? parsed2.segments[i] : 0;
    
    if (segment1 !== segment2) {
      return segment1 - segment2;
    }
  }
  
  return 0; // バージョンが等しい
}

/**
 * バージョンが親子関係にあるかを判定する
 * 例: isParentVersion("1.2", "1.2.3") => true
 *     isParentVersion("1.2", "1.3.0") => false
 */
export function isParentVersion(parent: string, child: string): boolean {
  const parentParsed = parseVersionString(parent);
  const childParsed = parseVersionString(child);
  
  // 子のセグメント数が親より少ない場合は親子関係にない
  if (childParsed.segments.length <= parentParsed.segments.length) {
    return false;
  }
  
  // 親のすべてのセグメントが子のセグメントと一致するか確認
  for (let i = 0; i < parentParsed.segments.length; i++) {
    if (parentParsed.segments[i] !== childParsed.segments[i]) {
      return false;
    }
  }
  
  return true;
}

/**
 * バージョン文字列を表示用にフォーマットする
 * 常にプレフィックス'v'を付けて返す
 */
export function formatVersionForDisplay(version: string): string {
  return parseVersionString(version).displayValue;
}

/**
 * VersionStateオブジェクトの配列からバージョン階層関係を構築する
 * 例: buildVersionHierarchy(["1.0", "1.1", "1.1.1", "1.2"]) =>
 * {
 *   "1.0": [],
 *   "1.1": ["1.1.1"],
 *   "1.2": []
 * }
 */
export function buildVersionHierarchy(versions: VersionState[]): Record<string, string[]> {
  const hierarchy: Record<string, string[]> = {};
  
  // 初期化
  versions.forEach(version => {
    hierarchy[version.id] = [];
  });
  
  // 親子関係の構築
  for (let i = 0; i < versions.length; i++) {
    const potentialChild = versions[i];
    
    for (let j = 0; j < versions.length; j++) {
      if (i === j) continue;
      
      const potentialParent = versions[j];
      
      if (isParentVersion(potentialParent.id, potentialChild.id)) {
        // 最も近い親を見つける
        let closestParent = potentialParent;
        let closestParentFound = false;
        
        for (let k = 0; k < versions.length; k++) {
          if (k === i || k === j) continue;
          
          const otherPotentialParent = versions[k];
          
          if (isParentVersion(otherPotentialParent.id, potentialChild.id) && 
              isParentVersion(potentialParent.id, otherPotentialParent.id)) {
            closestParent = otherPotentialParent;
            closestParentFound = true;
          }
        }
        
        if (!closestParentFound) {
          // 最も近い親の子リストに追加
          hierarchy[closestParent.id].push(potentialChild.id);
        }
      }
    }
  }
  
  return hierarchy;
}
