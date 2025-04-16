/**
 * asyncFeatureSchema.ts
 * 
 * 非同期処理に関する特性のスキーマを生成する関数
 */

import { AsyncFeature } from '../../../domain/schema.ts';

/**
 * 非同期処理特性スキーマを生成
 * 
 * @param options 非同期処理オプション
 * @returns 非同期処理特性スキーマ
 */
export function createAsyncFeatureSchema(options: AsyncFeature = {}): any {
  return {
    type: 'object',
    description: '非同期処理に関する特性',
    properties: {
      isAsync: {
        type: 'boolean',
        description: '非同期関数かどうか',
        default: false
      },
      asyncType: {
        type: 'string',
        enum: ['promise', 'observable', 'callback', 'stream', 'future'],
        description: '非同期の種類',
        default: 'promise'
      },
      awaitPattern: {
        type: 'object',
        description: '待機パターン',
        properties: {
          syntax: {
            type: 'string',
            enum: ['await', 'then', 'bind', 'custom'],
            description: '待機構文'
          },
          cancellable: {
            type: 'boolean',
            description: 'キャンセル可能かどうか',
            default: false
          }
        }
      }
    }
  };
}
