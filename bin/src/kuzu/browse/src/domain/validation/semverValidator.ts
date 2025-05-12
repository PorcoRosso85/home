/**
 * SemVerに準拠したバージョン文字列検証関数
 * 
 * TODO: 厳密なSemVer形式の検証を実装
 * TODO: 'v'プレフィックスの処理ルールを適用
 */

/**
 * 基本的なバージョン文字列の検証
 * x.y.z のような形式を検証（プレフィックス'v'は任意）
 */
export function isValidVersionFormat(version: string): boolean {
  // 'v'プレフィックスは無視して検証
  const versionWithoutPrefix = version.startsWith('v') ? version.substring(1) : version;
  
  // x.y.z の基本形式を検証する正規表現パターン
  const basicSemVerPattern = /^\d+(\.\d+)*$/;
  
  return basicSemVerPattern.test(versionWithoutPrefix);
}

/**
 * 完全なSemVer形式の検証（厳密モード）
 * MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD] の形式を検証
 */
export function isStrictSemVer(version: string): boolean {
  // 'v'プレフィックスは無視して検証
  const versionWithoutPrefix = version.startsWith('v') ? version.substring(1) : version;
  
  // SemVer 2.0の仕様に準拠した正規表現パターン
  const strictSemVerPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;
  
  return strictSemVerPattern.test(versionWithoutPrefix);
}

/**
 * バージョン文字列のセグメントを検証
 * 各セグメントが有効な数値であることを確認
 */
export function validateVersionSegments(version: string): { isValid: boolean; error?: string } {
  // 'v'プレフィックスは無視して検証
  const versionWithoutPrefix = version.startsWith('v') ? version.substring(1) : version;
  
  const segments = versionWithoutPrefix.split('.');
  
  // 少なくとも1つのセグメントが必要
  if (segments.length === 0) {
    return { isValid: false, error: 'バージョンは少なくとも1つのセグメントが必要です' };
  }
  
  // 各セグメントが有効な数値であることを確認
  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    
    // 空のセグメントをチェック
    if (segment.length === 0) {
      return { 
        isValid: false, 
        error: `セグメント ${i + 1} が空です` 
      };
    }
    
    // 数値以外の文字をチェック
    if (!/^\d+$/.test(segment)) {
      return { 
        isValid: false, 
        error: `セグメント ${i + 1} に数値以外の文字が含まれています` 
      };
    }
    
    // 先頭の不要なゼロをチェック
    if (segment.length > 1 && segment[0] === '0') {
      return { 
        isValid: false, 
        error: `セグメント ${i + 1} に不要な先頭のゼロが含まれています` 
      };
    }
  }
  
  return { isValid: true };
}

/**
 * エラーメッセージ付きでバージョン文字列を検証
 */
export function validateVersion(version: string): { isValid: boolean; error?: string } {
  if (!version || typeof version !== 'string') {
    return { isValid: false, error: 'バージョンは文字列である必要があります' };
  }
  
  // 基本フォーマットの検証
  if (!isValidVersionFormat(version)) {
    return { isValid: false, error: 'バージョンは x.y.z の形式である必要があります' };
  }
  
  // セグメントの詳細検証
  return validateVersionSegments(version);
}
