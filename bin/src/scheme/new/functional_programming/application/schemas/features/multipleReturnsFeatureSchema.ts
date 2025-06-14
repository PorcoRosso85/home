/**
 * multipleReturnsFeatureSchema.ts
 * 
 * 複数戻り値に関する特性のスキーマを生成する関数
 */

import { MultipleReturnsFeature } from '../../../domain/schema.ts';

/**
 * 複数戻り値特性スキーマを生成
 * 
 * @param options 複数戻り値オプション
 * @returns 複数戻り値特性スキーマ
 */
export function createMultipleReturnsFeatureSchema(options: MultipleReturnsFeature = {}): any {
  return {
    type: 'object',
    description: '複数戻り値に関する特性',
    properties: {
      multipleReturnValues: {
        type: 'boolean',
        description: '複数戻り値サポート',
        default: false
      },
      conditionalReturn: {
        type: 'object',
        description: '条件付き戻り値',
        properties: {
          conditions: {
            type: 'array',
            description: '条件リスト',
            items: {
              type: 'object',
              properties: {
                condition: {
                  type: 'string',
                  description: '条件の記述'
                },
                returnTypes: {
                  type: 'object',
                  description: '条件を満たす場合の戻り値型'
                }
              }
            }
          }
        }
      }
    }
  };
}
