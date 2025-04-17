/**
 * refCollector.ts
 * 
 * スキーマから$ref参照を収集するためのアプリケーション層のユーティリティ
 */

/**
 * スキーマから$ref参照を再帰的に収集する
 * 
 * @param schema JSONスキーマオブジェクト
 * @returns 収集された$ref参照のリスト
 */
export function collectReferences(schema: any): string[] {
  const refs: string[] = [];
  
  // 再帰的にオブジェクトを探索し$ref属性を収集
  function traverse(obj: any) {
    if (!obj || typeof obj !== 'object') {
      return;
    }
    
    // 配列の場合は各要素を再帰的に処理
    if (Array.isArray(obj)) {
      obj.forEach(item => traverse(item));
      return;
    }
    
    // $ref属性を検出した場合は結果に追加
    if (obj.$ref && typeof obj.$ref === 'string') {
      refs.push(obj.$ref);
    }
    
    // オブジェクトの各プロパティを再帰的に処理
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        traverse(obj[key]);
      }
    }
  }
  
  traverse(schema);
  
  // 重複を排除して返す
  return [...new Set(refs)].sort();
}

/**
 * メタスキーマ参照の形式に一致するかどうかを判定
 * 
 * @param ref 判定対象の参照文字列
 * @returns メタスキーマ参照の場合はtrue、それ以外はfalse
 */
export function isMetaSchemaReference(ref: string): boolean {
  return /^meta:\/\/[^/]+\/[^#]+#\/definitions\/.+$/.test(ref);
}

/**
 * 内部参照の形式に一致するかどうかを判定
 * 
 * @param ref 判定対象の参照文字列
 * @returns 内部参照の場合はtrue、それ以外はfalse
 */
export function isInternalReference(ref: string): boolean {
  return /^#\/.+/.test(ref);
}

/**
 * スキーマから外部メタスキーマへの参照のみを収集
 * 
 * @param schema JSONスキーマオブジェクト
 * @returns 外部メタスキーマへの参照のリスト
 */
export function collectExternalReferences(schema: any): string[] {
  const allRefs = collectReferences(schema);
  return allRefs.filter(ref => isMetaSchemaReference(ref));
}

/**
 * スキーマから内部参照のみを収集
 * 
 * @param schema JSONスキーマオブジェクト
 * @returns 内部参照のリスト
 */
export function collectInternalReferences(schema: any): string[] {
  const allRefs = collectReferences(schema);
  return allRefs.filter(ref => isInternalReference(ref));
}
