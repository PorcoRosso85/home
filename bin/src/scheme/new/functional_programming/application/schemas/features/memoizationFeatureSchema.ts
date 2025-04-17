/**
 * memoizationFeatureSchema.ts
 * 
 * メモ化に関する特性のスキーマを生成する関数
 */

import { MemoizationFeature } from '../../../domain/schema.ts';

/**
 * メモ化特性スキーマを生成
 * 
 * @param options メモ化オプション
 * @returns メモ化特性スキーマ
 */
export function createMemoizationFeatureSchema(options: MemoizationFeature = {}): any {
  return {
    type: 'object',
    description: 'メモ化に関する特性',
    properties: {
      supportsMemoization: {
        type: 'boolean',
        description: 'メモ化をサポートするかどうか',
        default: false
      },
      memoizationStrategy: {
        type: 'string',
        enum: ['simple', 'lru', 'custom'],
        description: 'メモ化戦略',
        default: 'simple'
      },
      memoizationScope: {
        type: 'string',
        enum: ['global', 'instance', 'call'],
        description: 'メモ化スコープ',
        default: 'instance'
      }
    }
  };
}
