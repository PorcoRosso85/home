/**
 * thrownExceptions.ts
 * 
 * 例外情報のスキーマを生成する関数
 */

/**
 * 例外定義
 */
export interface ThrownException {
  name: string;
  description: string;
  code?: string;
}

/**
 * 例外情報のスキーマを生成
 * 
 * @returns 例外情報のスキーマ
 */
export function createThrownExceptionsSchema(): any {
  return {
    type: 'array',
    description: '発生する可能性のある例外のリスト',
    items: {
      type: 'object',
      required: ['name', 'description'],
      properties: {
        name: {
          type: 'string',
          description: '例外の名前'
        },
        description: {
          type: 'string',
          description: '例外の説明'
        },
        code: {
          type: 'string',
          description: '例外コード (存在する場合)'
        }
      }
    }
  };
}
