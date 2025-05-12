/**
 * バージョン比較のためのユーティリティ関数
 * 
 * TODO: プレフィックス'v'を無視した比較を実装
 * TODO: SemVer準拠の比較ロジックを実装
 */

import { VERSION_COMPARE_RESULT } from '../../domain/constants/versionFormats';
import { parseVersionString } from '../../domain/service/versionParser';

/**
 * 2つのバージョン文字列を比較する
 * SemVer準拠の比較ロジックを使用
 * 
 * @returns {number} -1: v1 < v2, 0: v1 === v2, 1: v1 > v2
 */
export function compareVersions(v1: string, v2: string): number {
  // 'v'プレフィックスを無視して比較
  const parsed1 = parseVersionString(v1);
  const parsed2 = parseVersionString(v2);
  
  const minLength = Math.min(parsed1.segments.length, parsed2.segments.length);
  
  // 共通セグメントを比較
  for (let i = 0; i < minLength; i++) {
    if (parsed1.segments[i] < parsed2.segments[i]) {
      return VERSION_COMPARE_RESULT.LESS_THAN;
    }
    if (parsed1.segments[i] > parsed2.segments[i]) {
      return VERSION_COMPARE_RESULT.GREATER_THAN;
    }
  }
  
  // 共通セグメントが同じ場合、セグメント数で比較
  if (parsed1.segments.length < parsed2.segments.length) {
    return VERSION_COMPARE_RESULT.LESS_THAN;
  }
  if (parsed1.segments.length > parsed2.segments.length) {
    return VERSION_COMPARE_RESULT.GREATER_THAN;
  }
  
  // 完全に同じバージョン
  return VERSION_COMPARE_RESULT.EQUAL;
}

/**
 * バージョン配列をソートする
 * デフォルトは昇順（古い順）
 */
export function sortVersions(versions: string[], ascending = true): string[] {
  return [...versions].sort((a, b) => {
    const compareResult = compareVersions(a, b);
    return ascending ? compareResult : -compareResult;
  });
}

/**
 * 2つのバージョンが親子関係かどうかを判定
 * v1が親で、v2が子である場合にtrueを返す
 * 
 * 例: isParentChildRelationship('1.0', '1.0.1') => true
 *     isParentChildRelationship('1.0', '1.1.0') => false
 */
export function isParentChildRelationship(parent: string, child: string): boolean {
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
 * バージョン文字列の直近の親バージョンを計算する
 * 
 * 例: getParentVersion('1.2.3') => '1.2'
 *     getParentVersion('1.2') => '1'
 *     getParentVersion('1') => null
 */
export function getParentVersion(version: string): string | null {
  const parsed = parseVersionString(version);
  
  if (parsed.segments.length <= 1) {
    return null; // ルートバージョンには親がない
  }
  
  // 最後のセグメントを削除
  const parentSegments = parsed.segments.slice(0, -1);
  
  // 親バージョンを構築
  return parentSegments.join('.');
}

/**
 * 指定されたバージョンが特定の親バージョンの子孫かどうかを判定
 */
export function isDescendantOf(version: string, ancestor: string): boolean {
  let currentVersion = version;
  
  while (currentVersion) {
    const parent = getParentVersion(currentVersion);
    
    if (!parent) {
      return false; // ルートまで到達したが一致しなかった
    }
    
    if (parent === ancestor) {
      return true; // 祖先が見つかった
    }
    
    currentVersion = parent;
  }
  
  return false;
}
