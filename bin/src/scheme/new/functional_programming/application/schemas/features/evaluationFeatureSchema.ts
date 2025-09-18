/**
 * evaluationFeatureSchema.ts
 * 
 * 関数の評価に関する特性のスキーマを生成する関数
 */

import { EvaluationFeature } from '../../../domain/schema.ts';

/**
 * 関数の評価特性スキーマを生成
 * 
 * @param options 評価オプション
 * @returns 評価特性スキーマ
 */
export function createEvaluationFeatureSchema(options: EvaluationFeature = {}): any {
  return {
    type: 'object',
    description: '関数の評価に関する特性',
    properties: {
      isLazy: {
        type: 'boolean',
        description: '遅延評価が可能かどうか',
        default: false
      },
      lazyEvaluationStrategy: {
        type: 'string',
        enum: ['call-by-need', 'call-by-name'],
        description: '遅延評価戦略',
        default: 'call-by-need'
      },
      strictnessAnnotations: {
        type: 'boolean',
        description: '厳格性注釈サポート',
        default: false
      }
    }
  };
}
