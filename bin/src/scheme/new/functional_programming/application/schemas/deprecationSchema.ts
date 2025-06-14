/**
 * deprecationInfo.ts
 * 
 * 非推奨情報のスキーマを生成する関数
 */

/**
 * 非推奨情報スキーマを生成
 * 
 * @returns 非推奨情報スキーマのオブジェクト
 */
export function createDeprecatedSchema(): any {
  return {
    type: 'boolean',
    description: '関数が非推奨かどうか',
    default: false
  };
}

/**
 * 非推奨メッセージスキーマを生成
 * 
 * @returns 非推奨メッセージスキーマのオブジェクト
 */
export function createDeprecationMessageSchema(): any {
  return {
    type: 'string',
    description: '非推奨の場合のメッセージ'
  };
}
