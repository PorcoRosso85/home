/**
 * 共通ユーティリティ関数
 * 全層で使用される汎用的な関数
 */

/**
 * BigIntを含むオブジェクトをJSON.stringify可能な形式に変換
 * @param obj 変換対象のオブジェクト
 * @returns BigIntが変換されたオブジェクト
 */
export function serializeBigInt(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
  if (typeof obj === 'bigint') {
    // 安全な範囲内ならNumberに、超える場合は文字列に変換
    if (obj <= BigInt(Number.MAX_SAFE_INTEGER) && obj >= BigInt(Number.MIN_SAFE_INTEGER)) {
      return Number(obj);
    } else {
      return obj.toString();
    }
  }
  
  if (Array.isArray(obj)) {
    return obj.map(serializeBigInt);
  }
  
  if (typeof obj === 'object') {
    const result: Record<string, any> = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = serializeBigInt(value);
    }
    return result;
  }
  
  return obj;
}

/**
 * JSON.stringifyのラッパー（BigInt対応）
 * @param obj シリアライズ対象のオブジェクト
 * @param replacer 置換関数
 * @param space インデント
 * @returns JSON文字列
 */
export function safeJsonStringify(obj: any, replacer?: any, space?: string | number): string {
  const serialized = serializeBigInt(obj);
  return JSON.stringify(serialized, replacer, space);
}