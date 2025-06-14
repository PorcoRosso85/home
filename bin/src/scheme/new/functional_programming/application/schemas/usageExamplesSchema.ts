/**
 * usageExamples.ts
 * 
 * 使用例のスキーマを生成する関数
 */

/**
 * 使用例
 */
export interface UsageExample {
  description?: string;
  input: any;
  output: any;
  intermediateSteps?: Array<{
    stepName: string;
    value: any;
  }>;
}

/**
 * 使用例のスキーマを生成
 * 
 * @returns 使用例のスキーマ
 */
export function createUsageExamplesSchema(): any {
  return {
    type: 'array',
    description: '関数使用例',
    items: {
      type: 'object',
      required: ['input', 'output'],
      properties: {
        description: {
          type: 'string',
          description: '例の説明'
        },
        input: {
          description: '入力例'
        },
        output: {
          description: '期待される出力'
        },
        intermediateSteps: {
          type: 'array',
          description: '計算の各ステップでの中間結果',
          items: {
            type: 'object',
            properties: {
              stepName: {
                type: 'string',
                description: 'ステップの名前'
              },
              value: {
                description: '中間値'
              }
            }
          }
        }
      }
    }
  };
}
