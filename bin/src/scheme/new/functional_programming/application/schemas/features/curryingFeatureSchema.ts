/**
 * curryingFeatureSchema.ts
 * 
 * カリー化に関する特性のスキーマを生成する関数
 */

import { CurryingFeature } from '../../../domain/schema.ts';

/**
 * カリー化特性スキーマを生成
 * 
 * @param options カリー化オプション
 * @returns カリー化特性スキーマ
 */
export function createCurryingFeatureSchema(options: CurryingFeature = {}): any {
  return {
    type: 'object',
    description: 'カリー化に関する特性',
    properties: {
      isCurried: {
        type: 'boolean',
        description: 'カリー化された関数かどうか',
        default: false
      },
      partialApplicationSupport: {
        type: 'boolean',
        description: '部分適用サポート',
        default: false
      },
      curryingOrder: {
        type: 'string',
        enum: ['left-to-right', 'right-to-left'],
        description: 'カリー化順序',
        default: 'left-to-right'
      }
    }
  };
}
