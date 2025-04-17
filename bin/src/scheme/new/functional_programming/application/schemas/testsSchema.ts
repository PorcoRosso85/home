/**
 * @file testsSchema.ts
 * @description テスト情報のスキーマ生成関数
 */

import { TestsFeature } from "../../domain/features/tests/tests.ts";

/**
 * テスト情報のJSONスキーマを生成する関数
 * @param testsFeature テスト機能の定義
 * @returns JSONスキーマオブジェクト
 */
export const createTestsSchema = (testsFeature?: TestsFeature) => {
  if (!testsFeature) {
    return {
      type: "object",
      properties: {
        requiresTests: {
          type: "boolean",
          description: "テストが必要かどうかのフラグ",
          default: false
        }
      }
    };
  }

  return {
    type: "object",
    description: "関数のテスト仕様と要件",
    required: ["requiresTests"],
    properties: {
      requiresTests: {
        type: "boolean",
        description: "テストが必要かどうかのフラグ",
        default: false
      },
      testCaseGeneration: {
        type: "object",
        description: "テストケース生成のヒント情報",
        properties: {
          edgeCases: {
            type: "array",
            description: "エッジケースの識別情報",
            items: {
              type: "object",
              required: ["description"],
              properties: {
                description: {
                  type: "string",
                  description: "エッジケースの説明"
                },
                input: {
                  description: "エッジケースのテスト入力"
                },
                expectedOutput: {
                  description: "エッジケースの期待される出力"
                }
              }
            }
          },
          boundaryConditions: {
            type: "array",
            description: "境界条件の明示",
            items: {
              type: "object",
              required: ["description"],
              properties: {
                description: {
                  type: "string",
                  description: "境界条件の説明"
                },
                input: {
                  description: "境界条件のテスト入力"
                },
                expectedOutput: {
                  description: "境界条件の期待される出力"
                }
              }
            }
          },
          essentialHappyPath: {
            type: "object",
            description: "必須の正常系テストケース",
            required: ["description"],
            properties: {
              description: {
                type: "string",
                description: "テストケースの説明"
              },
              input: {
                description: "テスト入力"
              },
              expectedOutput: {
                description: "期待される出力"
              },
              motivation: {
                type: "string",
                description: "このテストケースが重要な理由"
              }
            }
          }
        }
      },
      propertyBasedTesting: {
        type: "object",
        description: "プロパティベーステストの戦略",
        properties: {
          inputProperties: {
            type: "array",
            description: "生成すべき入力の性質",
            items: {
              type: "object",
              required: ["property", "description"],
              properties: {
                property: {
                  type: "string",
                  description: "入力プロパティの名前"
                },
                description: {
                  type: "string",
                  description: "入力プロパティの説明"
                }
              }
            }
          },
          invariants: {
            type: "array",
            description: "不変条件の定義",
            items: {
              type: "object",
              required: ["description"],
              properties: {
                description: {
                  type: "string",
                  description: "不変条件の説明"
                },
                condition: {
                  type: "string",
                  description: "不変条件を表す擬似コード"
                }
              }
            }
          }
        }
      },
      testability: {
        type: "object",
        description: "テスト容易性の評価基準",
        properties: {
          mockability: {
            type: "object",
            description: "モック化の可能性",
            required: ["score"],
            properties: {
              score: {
                type: "integer",
                minimum: 1,
                maximum: 10,
                description: "モック容易性スコア (1-10)"
              },
              description: {
                type: "string",
                description: "モック化に関する詳細説明"
              }
            }
          },
          isolationStrategy: {
            type: "object",
            description: "分離テスト戦略",
            required: ["description"],
            properties: {
              description: {
                type: "string",
                description: "分離テスト戦略の説明"
              },
              dependencies: {
                type: "array",
                description: "テスト時に考慮すべき依存関係",
                items: {
                  type: "string"
                }
              }
            }
          }
        }
      }
    }
  };
};
