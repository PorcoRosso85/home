/**
 * externalDependencies.ts
 * 
 * 外部依存関係のスキーマを生成する関数
 */

/**
 * 外部依存関係
 */
export interface ExternalDependency {
  $ref: string;
  description?: string;
}

/**
 * 外部依存関係のスキーマを生成
 * 
 * @returns 外部依存関係のスキーマ
 */
export function createExternalDependenciesSchema(): any {
  return {
    type: 'array',
    description: '関数が依存する外部関数のリスト',
    items: {
      type: 'object',
      required: ['$ref'],
      properties: {
        $ref: {
          type: 'string',
          description: '依存関数のスキーマへの参照'
        },
        description: {
          type: 'string',
          description: '依存関係の説明（任意）'
        }
      },
      additionalProperties: false
    }
  };
}
