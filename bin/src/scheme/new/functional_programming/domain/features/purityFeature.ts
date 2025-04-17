/**
 * purityFeature.ts
 * 
 * 関数の純粋性に関する特性のスキーマを生成する関数
 */

/**
 * 関数の純粋性に関する特性
 */
export interface PurityFeature {
  isPure?: boolean;
  referentiallyTransparent?: boolean;
  sideEffects?: Array<{
    type: string;
    description: string;
  }>;
}

/**
 * 関数の純粋性特性スキーマを生成
 * 
 * @param options 純粋性オプション
 * @returns 純粋性特性スキーマ
 */
export function createPurityFeatureSchema(options: PurityFeature = {}): any {
  return {
    type: 'object',
    description: '関数の純粋性に関する特性',
    properties: {
      isPure: {
        type: 'boolean',
        description: '純粋関数かどうか（同じ入力に対して常に同じ出力を返し、副作用がない）',
        default: true
      },
      referentiallyTransparent: {
        type: 'boolean',
        description: '参照透過性',
        default: true
      },
      sideEffects: {
        type: 'array',
        description: '副作用の詳細リスト',
        items: {
          type: 'object',
          properties: {
            type: {
              type: 'string',
              description: '副作用の種類'
            },
            description: {
              type: 'string',
              description: '副作用の説明'
            }
          }
        }
      }
    }
  };
}
