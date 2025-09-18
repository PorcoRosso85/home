/**
 * signatureSchema.ts
 * 
 * 関数シグネチャのスキーマを生成する関数
 */

/**
 * パラメータ型定義のスキーマを生成
 * 
 * @returns パラメータ型定義のスキーマ
 */
export function createParameterTypeSchema(): any {
  return {
    type: 'object',
    description: '関数の入力パラメータの型',
    required: ['type'],
    properties: {
      type: {
        type: 'string',
        description: 'パラメータの型'
      },
      description: {
        type: 'string',
        description: 'パラメータの説明'
      },
      $ref: {
        type: 'string',
        description: '別のスキーマへの参照'
      },
      items: {
        type: 'object',
        description: '配列要素の定義 (配列の場合)'
      },
      properties: {
        type: 'object',
        description: 'オブジェクトプロパティの定義 (オブジェクトの場合)'
      },
      immutable: {
        type: 'boolean',
        description: 'パラメータが不変かどうか',
        default: true
      },
      required: {
        type: 'array',
        items: {
          type: 'string'
        },
        description: '必須パラメータのリスト'
      },
      propertiesOrder: {
        type: 'array',
        items: {
          type: 'string'
        },
        description: 'パラメータの順序'
      },
      varargs: {
        type: 'boolean',
        description: '可変長引数サポート',
        default: false
      },
      defaultsStrategy: {
        type: 'string',
        enum: ['eager', 'lazy', 'none'],
        description: 'デフォルト値の評価戦略',
        default: 'eager'
      },
      // 共用型（Union型）のサポート
      variants: {
        type: 'array',
        description: '共用型（Union型）の候補となる型のリスト',
        items: {
          type: 'object',
          description: '型の選択肢',
          required: ['type'],
          properties: {
            type: {
              type: 'string',
              description: '型の名前'
            },
            description: {
              type: 'string',
              description: 'この型の選択肢の説明'
            },
            $ref: {
              type: 'string',
              description: '外部スキーマへの参照'
            },
            properties: {
              type: 'object',
              description: 'オブジェクト型の場合のプロパティ定義'
            }
          }
        }
      }
    }
  };
}

/**
 * 戻り値型定義のスキーマを生成
 * 
 * @returns 戻り値型定義のスキーマ
 */
export function createReturnTypeSchema(): any {
  return {
    type: 'object',
    description: '関数の戻り値の型',
    required: ['type'],
    properties: {
      type: {
        type: 'string',
        description: '戻り値の型'
      },
      description: {
        type: 'string',
        description: '戻り値の説明'
      },
      $ref: {
        type: 'string',
        description: '別のスキーマへの参照'
      },
      items: {
        type: 'object',
        description: '配列要素の定義 (配列の場合)'
      },
      properties: {
        type: 'object',
        description: 'オブジェクトプロパティの定義 (オブジェクトの場合)'
      },
      immutable: {
        type: 'boolean',
        description: '戻り値が不変かどうか',
        default: true
      },
      // 共用型（Union型）のサポート
      variants: {
        type: 'array',
        description: '共用型（Union型）の候補となる型のリスト',
        items: {
          type: 'object',
          description: '型の選択肢',
          required: ['type'],
          properties: {
            type: {
              type: 'string',
              description: '型の名前'
            },
            description: {
              type: 'string',
              description: 'この型の選択肢の説明'
            },
            $ref: {
              type: 'string',
              description: '外部スキーマへの参照'
            },
            properties: {
              type: 'object',
              description: 'オブジェクト型の場合のプロパティ定義'
            }
          }
        }
      }
    }
  };
}

/**
 * 関数シグネチャスキーマを生成
 * 
 * @returns シグネチャスキーマオブジェクト
 */
export function createSignatureSchema(): any {
  return {
    type: 'object',
    required: ['id', 'parameterTypes', 'returnTypes'],
    properties: {
      id: {
        type: 'string',
        description: 'シグネチャの識別子'
      },
      description: {
        type: 'string',
        description: 'シグネチャの説明'
      },
      parameterTypes: createParameterTypeSchema(),
      returnTypes: createReturnTypeSchema()
    }
  };
}

/**
 * 関数シグネチャのリストスキーマを生成
 * 
 * @returns シグネチャリストスキーマオブジェクト
 */
export function createSignaturesListSchema(): any {
  return {
    type: 'array',
    description: '関数のシグネチャ（引数型と戻り値型のペア）リスト',
    minItems: 1,
    items: createSignatureSchema()
  };
}
