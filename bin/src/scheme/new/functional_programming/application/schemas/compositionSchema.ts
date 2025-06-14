/**
 * 関数合成情報のスキーマ生成機能
 */
import { CompositionFeature } from '../../domain/features/composition.ts';

/**
 * 関数合成情報のJSONスキーマを生成する
 * @returns 関数合成情報のJSONスキーマ
 */
export function createCompositionSchema() {
  return {
    type: "object",
    description: "関数の合成に関する情報",
    properties: {
      composable: {
        type: "boolean",
        description: "この関数が他の関数と簡単に合成可能かどうか"
      },
      compositionPatterns: {
        type: "array",
        description: "この関数が対応する合成パターン",
        items: {
          type: "string",
          enum: ["pipeline", "pointfree", "monad", "applicative", "arrow", "lens", "transducer"]
        }
      },
      dataFlow: {
        type: "object",
        description: "関数間のデータフロー情報",
        properties: {
          inputTransformations: {
            type: "array",
            description: "入力データの変換ステップ",
            items: {
              type: "object",
              properties: {
                stage: { type: "string" },
                description: { type: "string" },
                dependencies: {
                  type: "array",
                  items: { type: "string" }
                }
              },
              required: ["stage", "description"]
            }
          },
          outputAdaptations: {
            type: "array",
            description: "出力データの適応パターン",
            items: {
              type: "object",
              properties: {
                pattern: { type: "string" },
                description: { type: "string" }
              },
              required: ["pattern", "description"]
            }
          }
        }
      },
      optimizationHints: {
        type: "object",
        description: "合成時の最適化ヒント",
        properties: {
          fusable: { type: "boolean" },
          parallelizable: { type: "boolean" },
          memoizable: { type: "boolean" },
          notes: { type: "string" }
        },
        required: ["fusable", "parallelizable", "memoizable"]
      }
    },
    required: ["composable"]
  };
}

/**
 * 既存のスキーマに関数合成情報を統合する
 * @param baseSchema 基本スキーマ
 * @returns 合成情報を追加したスキーマ
 */
export function integrateCompositionSchema(baseSchema: any) {
  return {
    ...baseSchema,
    properties: {
      ...baseSchema.properties,
      composition: createCompositionSchema()
    }
  };
}

/**
 * サンプル実装例: mapと合成可能な関数の合成情報
 */
export const sampleCompositionData: CompositionFeature = {
  composable: true,
  compositionPatterns: ["pipeline", "pointfree", "transducer"],
  dataFlow: {
    inputTransformations: [
      {
        stage: "validation",
        description: "入力データの検証を行う",
        dependencies: []
      },
      {
        stage: "normalization",
        description: "データの正規化を行う",
        dependencies: ["validation"]
      }
    ],
    outputAdaptations: [
      {
        pattern: "unwrap",
        description: "Maybe/Eitherなどの型からの値の取り出し"
      }
    ]
  },
  optimizationHints: {
    fusable: true,
    parallelizable: true,
    memoizable: true,
    notes: "map操作と融合可能、純粋関数のため安全にメモ化可能"
  }
};
