/**
 * featureSchema.ts
 * 
 * 機能特性のスキーマを生成する関数
 */

import { FunctionFeatures } from '../../domain/features/index.ts';
import { createTypeSystemSchema } from './typeSystemSchema.ts';

/**
 * 機能特性スキーマを生成
 * 
 * @param features 関数の機能特性
 * @returns 機能特性のスキーマ
 */
export function createFeaturesSchema(features: FunctionFeatures = {}): any {
  const featuresSchema: any = {
    type: 'object',
    description: '関数の機能特性',
    properties: {}
  };

  // 純粋性の特性
  if (features.purity) {
    featuresSchema.properties.purity = {
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

  // 評価戦略の特性
  if (features.evaluation) {
    featuresSchema.properties.evaluation = {
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

  // カリー化の特性
  if (features.currying) {
    featuresSchema.properties.currying = {
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
          default: true
        },
        curryingOrder: {
          type: 'string',
          enum: ['left-to-right', 'right-to-left'],
          description: 'カリー化の順序',
          default: 'left-to-right'
        }
      }
    };
  }

  // 再帰の特性
  if (features.recursion) {
    featuresSchema.properties.recursion = {
      type: 'object',
      description: '再帰に関する特性',
      properties: {
        isRecursive: {
          type: 'boolean',
          description: '関数が再帰的か',
          default: false
        },
        recursionLimit: {
          type: ['number', 'null'],
          description: '再帰の制限（ある場合）',
          default: null
        },
        tailRecursive: {
          type: 'boolean',
          description: '末尾再帰最適化が適用可能か',
          default: false
        },
        recursionType: {
          type: 'string',
          enum: ['direct', 'mutual', 'nested'],
          description: '再帰の種類',
          default: 'direct'
        },
        terminationCondition: {
          type: 'string',
          description: '終了条件'
        },
        terminationProof: {
          type: 'object',
          description: '終了証明',
          properties: {
            measure: {
              type: 'string',
              description: '測度関数'
            },
            argument: {
              type: 'string',
              description: '減少引数'
            }
          }
        },
        complexityAnalysis: {
          type: 'object',
          properties: {
            time: {
              type: 'string',
              description: '時間計算量'
            },
            space: {
              type: 'string',
              description: '空間計算量'
            }
          }
        },
        recursionDepth: {
          type: 'object',
          properties: {
            maximum: {
              type: 'number',
              description: '最大再帰深度'
            },
            average: {
              type: 'number',
              description: '平均再帰深度'
            },
            description: {
              type: 'string',
              description: '再帰深度についての説明'
            }
          }
        },
        mutuallyRecursiveWith: {
          type: 'array',
          description: '相互再帰関数のリスト',
          items: {
            type: 'object',
            properties: {
              name: {
                type: 'string',
                description: '関数名'
              },
              $ref: {
                type: 'string',
                description: '関数への参照'
              }
            }
          }
        },
        invariants: {
          type: 'array',
          items: {
            type: 'string'
          },
          description: '再帰不変条件'
        },
        transformationType: {
          type: 'array',
          items: {
            type: 'string',
            enum: ['tailCall', 'accumulator', 'trampolined', 'none']
          },
          description: '変換の種類'
        },
        structuralRecursion: {
          type: 'boolean',
          description: '構造的再帰かどうか',
          default: false
        }
      }
    };
  }

  // メモ化の特性
  if (features.memoization) {
    featuresSchema.properties.memoization = {
      type: 'object',
      description: 'メモ化に関する特性',
      properties: {
        supportsMemoization: {
          type: 'boolean',
          description: 'メモ化をサポートするか',
          default: false
        },
        memoizationStrategy: {
          type: 'string',
          enum: ['simple', 'lru', 'custom'],
          description: 'メモ化の戦略',
          default: 'simple'
        },
        memoizationScope: {
          type: 'string',
          enum: ['global', 'instance', 'call'],
          description: 'メモ化のスコープ',
          default: 'call'
        }
      }
    };
  }

  // 非同期処理の特性
  if (features.async) {
    featuresSchema.properties.async = {
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
          description: '非同期処理の種類',
          default: 'promise'
        },
        awaitPattern: {
          type: 'object',
          properties: {
            syntax: {
              type: 'string',
              enum: ['await', 'then', 'bind', 'custom'],
              description: '待機パターンの構文',
              default: 'await'
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

  // 複数戻り値の特性
  if (features.multipleReturns) {
    featuresSchema.properties.multipleReturns = {
      type: 'object',
      description: '複数戻り値に関する特性',
      properties: {
        multipleReturnValues: {
          type: 'boolean',
          description: '複数の戻り値をサポートするか',
          default: false
        },
        conditionalReturn: {
          type: 'object',
          properties: {
            conditions: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  condition: {
                    type: 'string',
                    description: '条件の説明'
                  },
                  returnTypes: {
                    type: 'object',
                    description: '戻り値の型'
                  }
                }
              }
            }
          }
        }
      }
    };
  }

  // 型システムの特性
  if (features.typeSystem) {
    const typeSystemSchema = createTypeSystemSchema(features.typeSystem);
    if (typeSystemSchema) {
      featuresSchema.properties.typeSystem = typeSystemSchema;
    }
  }

  return featuresSchema;
}
