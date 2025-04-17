/**
 * recursionFeatureSchema.ts
 * 
 * 再帰に関する特性のスキーマを生成する関数
 */

import { RecursionFeature } from '../../../domain/schema.ts';

/**
 * 再帰特性スキーマを生成
 * 
 * @param options 再帰オプション
 * @returns 再帰特性スキーマ
 */
export function createRecursionFeatureSchema(options: RecursionFeature = {}): any {
  return {
    type: 'object',
    description: '再帰に関する特性',
    properties: {
      isRecursive: {
        type: 'boolean',
        description: '関数が再帰的かどうか',
        default: false
      },
      recursionLimit: {
        type: 'number',
        description: '再帰制限',
        default: null
      },
      tailRecursive: {
        type: 'boolean',
        description: '末尾再帰最適化が可能かどうか',
        default: false
      },
      recursionType: {
        type: 'string',
        enum: ['direct', 'mutual', 'nested'],
        description: '再帰の種類（直接再帰、相互再帰、入れ子再帰）',
        default: 'direct'
      },
      terminationCondition: {
        type: 'string',
        description: '再帰の終了条件の説明'
      },
      terminationProof: {
        type: 'object',
        description: '終了性証明',
        properties: {
          measure: {
            type: 'string',
            description: '終了性を示す測度関数'
          },
          argument: {
            type: 'string',
            description: '終了性の論証'
          }
        }
      },
      complexityAnalysis: {
        type: 'object',
        description: '再帰の計算量分析',
        properties: {
          time: {
            type: 'string',
            description: '時間計算量（例: O(n), O(2^n)）'
          },
          space: {
            type: 'string',
            description: '空間計算量（例: O(n), O(log n)）'
          }
        }
      },
      recursionDepth: {
        type: 'object',
        description: '再帰の深さに関する情報',
        properties: {
          maximum: {
            type: 'integer',
            description: '想定される最大再帰深度'
          },
          average: {
            type: 'number',
            description: '平均的な再帰深度'
          },
          description: {
            type: 'string',
            description: '再帰深度に関する追加情報'
          }
        }
      },
      mutuallyRecursiveWith: {
        type: 'array',
        description: '相互再帰している関数のリスト',
        items: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: '相互再帰関数の名前'
            },
            $ref: {
              type: 'string',
              description: '相互再帰関数への参照'
            }
          }
        }
      },
      invariants: {
        type: 'array',
        description: '再帰の不変条件',
        items: {
          type: 'string',
          description: '再帰中に維持される条件の説明'
        }
      },
      transformationType: {
        type: 'array',
        description: '再帰から反復への変換可能性',
        items: {
          type: 'string',
          enum: ['tailCall', 'accumulator', 'trampolined', 'none'],
          description: '変換タイプ（末尾呼び出し最適化、蚀積変数使用、トランポリン使用可能）'
        }
      },
      structuralRecursion: {
        type: 'boolean',
        description: '構造的再帰かどうか（入力データ構造に対して構造的に分解していく再帰）',
        default: false
      }
    }
  };
}
