/**
 * typeSystemSchema.ts
 * 
 * 型システムのスキーマを生成する関数
 */

import { 
  TypeSystemFeature, 
  AlgebraicDataTypeFeature, 
  GenericTypeFeature, 
  DependentTypeFeature 
} from '../../domain/features/typeSystem.ts';
import {
  TypeLevelProgrammingFeature,
  SingletonTypeFeature,
  RefinementTypeFeature
} from '../../domain/features/dependentTypes.ts';
import {
  createExtendedDependentTypeSchema
} from './dependentTypeSchema.ts';

/**
 * 代数的データ型（ADT）のスキーマを生成する
 * 
 * @param feature ADT機能特性オブジェクト
 * @returns ADTスキーマ
 */
export function createAlgebraicDataTypeSchema(feature?: AlgebraicDataTypeFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: '代数的データ型（ADT）のサポート情報',
    properties: {}
  };

  // サム型のスキーマ
  if (feature.sumTypes) {
    schema.properties.sumTypes = {
      type: 'object',
      description: 'サム型（直和型）のサポート',
      properties: {
        supported: {
          type: 'boolean',
          description: 'サム型がサポートされているか',
          default: false
        }
      }
    };

    // 表現方法
    if (feature.sumTypes.representation) {
      schema.properties.sumTypes.properties.representation = {
        type: 'string',
        enum: ['tagged-union', 'variant-record', 'polymorphic-variant', 'custom'],
        description: 'サム型の表現方法',
        default: 'tagged-union'
      };
    }

    // 例
    if (feature.sumTypes.examples) {
      schema.properties.sumTypes.properties.examples = {
        type: 'array',
        items: {
          type: 'string'
        },
        description: 'サム型の例'
      };
    }
  }

  // プロダクト型のスキーマ
  if (feature.productTypes) {
    schema.properties.productTypes = {
      type: 'object',
      description: 'プロダクト型（直積型）のサポート',
      properties: {
        supported: {
          type: 'boolean',
          description: 'プロダクト型がサポートされているか',
          default: false
        }
      }
    };

    // 表現方法
    if (feature.productTypes.representation) {
      schema.properties.productTypes.properties.representation = {
        type: 'string',
        enum: ['tuple', 'record', 'class', 'custom'],
        description: 'プロダクト型の表現方法',
        default: 'record'
      };
    }

    // 例
    if (feature.productTypes.examples) {
      schema.properties.productTypes.properties.examples = {
        type: 'array',
        items: {
          type: 'string'
        },
        description: 'プロダクト型の例'
      };
    }
  }

  // パターンマッチングのスキーマ
  if (feature.patternMatching) {
    schema.properties.patternMatching = {
      type: 'object',
      description: 'パターンマッチングのサポート',
      properties: {
        supported: {
          type: 'boolean',
          description: 'パターンマッチングがサポートされているか',
          default: false
        }
      }
    };

    // 網羅性チェック
    if (feature.patternMatching.exhaustivenessChecking !== undefined) {
      schema.properties.patternMatching.properties.exhaustivenessChecking = {
        type: 'boolean',
        description: '網羅性チェックがサポートされているか',
        default: false
      };
    }

    // ネストされたパターン
    if (feature.patternMatching.nestedPatterns !== undefined) {
      schema.properties.patternMatching.properties.nestedPatterns = {
        type: 'boolean',
        description: 'ネストされたパターンがサポートされているか',
        default: false
      };
    }

    // ガード式
    if (feature.patternMatching.guardExpressions !== undefined) {
      schema.properties.patternMatching.properties.guardExpressions = {
        type: 'boolean',
        description: 'ガード式がサポートされているか',
        default: false
      };
    }
  }

  return schema;
}

/**
 * ジェネリック型のスキーマを生成する
 * 
 * @param feature ジェネリック型機能特性オブジェクト
 * @returns ジェネリック型スキーマ
 */
export function createGenericTypeSchema(feature?: GenericTypeFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: 'ジェネリック型のサポート情報',
    properties: {
      supported: {
        type: 'boolean',
        description: 'ジェネリック型がサポートされているか',
        default: false
      }
    }
  };

  // 型パラメータのスキーマ
  if (feature.typeParameters) {
    schema.properties.typeParameters = {
      type: 'object',
      description: '型パラメータのサポート',
      properties: {}
    };

    // 変性
    if (feature.typeParameters.variance) {
      schema.properties.typeParameters.properties.variance = {
        type: 'string',
        enum: ['invariant', 'covariant', 'contravariant', 'bivariant'],
        description: '型パラメータの変性',
        default: 'invariant'
      };
    }

    // 制約
    if (feature.typeParameters.constraints) {
      schema.properties.typeParameters.properties.constraints = {
        type: 'object',
        description: '型パラメータの制約',
        properties: {
          supported: {
            type: 'boolean',
            description: '型制約がサポートされているか',
            default: false
          }
        }
      };

      // 制約メカニズム
      if (feature.typeParameters.constraints.constraintMechanisms) {
        schema.properties.typeParameters.properties.constraints.properties.constraintMechanisms = {
          type: 'array',
          items: {
            type: 'string',
            enum: ['subtyping', 'typeclasses', 'interfaces', 'concepts', 'custom']
          },
          description: 'サポートされている制約メカニズム'
        };
      }
    }
  }

  // 高階型のスキーマ
  if (feature.higherKindedTypes) {
    schema.properties.higherKindedTypes = {
      type: 'object',
      description: '高階型のサポート',
      properties: {
        supported: {
          type: 'boolean',
          description: '高階型がサポートされているか',
          default: false
        }
      }
    };

    // 最大カインドレベル
    if (feature.higherKindedTypes.maxKindLevel !== undefined) {
      schema.properties.higherKindedTypes.properties.maxKindLevel = {
        type: 'integer',
        description: 'サポートされている最大の型カインドレベル',
        default: 1
      };
    }

    // 例
    if (feature.higherKindedTypes.examples) {
      schema.properties.higherKindedTypes.properties.examples = {
        type: 'array',
        items: {
          type: 'string'
        },
        description: '高階型の例'
      };
    }
  }

  return schema;
}

/**
 * 依存型のスキーマを生成する
 * 
 * @param feature 依存型機能特性オブジェクト
 * @returns 依存型スキーマ
 */
export function createDependentTypeSchema(feature?: DependentTypeFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: '依存型のサポート情報',
    properties: {
      supported: {
        type: 'boolean',
        description: '依存型がサポートされているか',
        default: false
      }
    }
  };

  // 値によるインデックス化
  if (feature.valueIndexing) {
    schema.properties.valueIndexing = {
      type: 'object',
      description: '値による型のインデックス化',
      properties: {
        supported: {
          type: 'boolean',
          description: '値による型のインデックス化がサポートされているか',
          default: false
        }
      }
    };

    // 式の制限
    if (feature.valueIndexing.expressionRestrictions) {
      schema.properties.valueIndexing.properties.expressionRestrictions = {
        type: 'string',
        description: 'インデックスに使用できる式の制限'
      };
    }

    // 許可される値の種類
    if (feature.valueIndexing.allowedValueTypes) {
      schema.properties.valueIndexing.properties.allowedValueTypes = {
        type: 'array',
        items: {
          type: 'string',
          enum: ['constant', 'parameter', 'computed', 'global']
        },
        description: '型が依存できる値の種類'
      };
    }

    // 依存の方向性
    if (feature.valueIndexing.dependencyDirection) {
      schema.properties.valueIndexing.properties.dependencyDirection = {
        type: 'string',
        enum: ['value-to-type', 'type-to-value', 'bidirectional'],
        description: '型依存の方向性'
      };
    }
  }

  // 洗練型
  if (feature.refinementTypes) {
    schema.properties.refinementTypes = {
      type: 'object',
      description: '洗練型のサポート',
      properties: {
        supported: {
          type: 'boolean',
          description: '洗練型がサポートされているか',
          default: false
        }
      }
    };

    // 静的検証
    if (feature.refinementTypes.staticVerification !== undefined) {
      schema.properties.refinementTypes.properties.staticVerification = {
        type: 'boolean',
        description: '静的検証がサポートされているか',
        default: false
      };
    }

    // 動的検証
    if (feature.refinementTypes.dynamicVerification !== undefined) {
      schema.properties.refinementTypes.properties.dynamicVerification = {
        type: 'boolean',
        description: '動的検証がサポートされているか',
        default: false
      };
    }

    // 式の複雑さ
    if (feature.refinementTypes.expressionComplexity) {
      schema.properties.refinementTypes.properties.expressionComplexity = {
        type: 'string',
        enum: ['simple', 'moderate', 'complex'],
        description: '洗練型の式の複雑さ',
        default: 'simple'
      };
    }

    // 述語言語
    if (feature.refinementTypes.predicateLanguage) {
      schema.properties.refinementTypes.properties.predicateLanguage = {
        type: 'string',
        description: '述語言語の説明'
      };
    }

    // 述語の例
    if (feature.refinementTypes.examplePredicates) {
      schema.properties.refinementTypes.properties.examplePredicates = {
        type: 'array',
        items: {
          type: 'string'
        },
        description: '述語の例'
      };
    }
  }

  // 型レベル計算
  if (feature.typeLevelComputation) {
    schema.properties.typeLevelComputation = {
      type: 'object',
      description: '型レベル計算',
      properties: {
        supported: {
          type: 'boolean',
          description: '型レベル計算がサポートされているか',
          default: false
        }
      }
    };

    // 再帰
    if (feature.typeLevelComputation.recursion !== undefined) {
      schema.properties.typeLevelComputation.properties.recursion = {
        type: 'boolean',
        description: '型レベル再帰がサポートされているか',
        default: false
      };
    }

    // 例
    if (feature.typeLevelComputation.examples) {
      schema.properties.typeLevelComputation.properties.examples = {
        type: 'array',
        items: {
          type: 'string'
        },
        description: '型レベル計算の例'
      };
    }

    // 型レベル関数
    if (feature.typeLevelComputation.typeFunctions) {
      schema.properties.typeLevelComputation.properties.typeFunctions = {
        type: 'object',
        description: '型レベル関数',
        properties: {
          supported: {
            type: 'boolean',
            description: '型レベル関数がサポートされているか',
            default: false
          }
        }
      };

      const typeFunctionsProps = schema.properties.typeLevelComputation.properties.typeFunctions.properties;

      // 高階関数
      if (feature.typeLevelComputation.typeFunctions.higherOrder !== undefined) {
        typeFunctionsProps.higherOrder = {
          type: 'boolean',
          description: '高階型関数がサポートされているか',
          default: false
        };
      }

      // 再帰的定義
      if (feature.typeLevelComputation.typeFunctions.recursiveDefinitions !== undefined) {
        typeFunctionsProps.recursiveDefinitions = {
          type: 'boolean',
          description: '再帰的な型関数定義がサポートされているか',
          default: false
        };
      }

      // 適用構文
      if (feature.typeLevelComputation.typeFunctions.applicationSyntax) {
        typeFunctionsProps.applicationSyntax = {
          type: 'string',
          description: '型適用の構文例'
        };
      }
    }

    // 型レベル条件分岐
    if (feature.typeLevelComputation.conditionals) {
      schema.properties.typeLevelComputation.properties.conditionals = {
        type: 'object',
        description: '型レベル条件分岐',
        properties: {
          supported: {
            type: 'boolean',
            description: '型レベル条件分岐がサポートされているか',
            default: false
          }
        }
      };

      const conditionalsProps = schema.properties.typeLevelComputation.properties.conditionals.properties;

      // if-then-else
      if (feature.typeLevelComputation.conditionals.ifThenElse !== undefined) {
        conditionalsProps.ifThenElse = {
          type: 'boolean',
          description: 'if-then-else条件分岐がサポートされているか',
          default: false
        };
      }

      // パターンマッチング
      if (feature.typeLevelComputation.conditionals.patternMatching !== undefined) {
        conditionalsProps.patternMatching = {
          type: 'boolean',
          description: 'パターンマッチングによる条件分岐がサポートされているか',
          default: false
        };
      }

      // ガード型
      if (feature.typeLevelComputation.conditionals.guardedTypes !== undefined) {
        conditionalsProps.guardedTypes = {
          type: 'boolean',
          description: 'ガード式による型条件分岐がサポートされているか',
          default: false
        };
      }
    }
  }

  // シングルトン型
  if (feature.singletonTypes) {
    schema.properties.singletonTypes = {
      type: 'object',
      description: 'シングルトン型',
      properties: {
        supported: {
          type: 'boolean',
          description: 'シングルトン型がサポートされているか',
          default: false
        }
      }
    };

    // リテラル型
    if (feature.singletonTypes.literalTypes) {
      schema.properties.singletonTypes.properties.literalTypes = {
        type: 'array',
        items: {
          type: 'string',
          enum: ['number', 'string', 'boolean', 'symbol', 'custom']
        },
        description: 'サポートされているリテラル型'
      };
    }

    // 値の昇格
    if (feature.singletonTypes.promotedValues !== undefined) {
      schema.properties.singletonTypes.properties.promotedValues = {
        type: 'boolean',
        description: '値の型レベルへの昇格がサポートされているか',
        default: false
      };
    }
  }

  // 依存関数型
  if (feature.dependentFunctionTypes) {
    schema.properties.dependentFunctionTypes = {
      type: 'object',
      description: '依存関数型',
      properties: {
        supported: {
          type: 'boolean',
          description: '依存関数型がサポートされているか',
          default: false
        }
      }
    };

    // Pi型
    if (feature.dependentFunctionTypes.piTypes !== undefined) {
      schema.properties.dependentFunctionTypes.properties.piTypes = {
        type: 'boolean',
        description: 'Pi型がサポートされているか',
        default: false
      };
    }

    // パラメータ依存
    if (feature.dependentFunctionTypes.dependentParameters !== undefined) {
      schema.properties.dependentFunctionTypes.properties.dependentParameters = {
        type: 'boolean',
        description: 'パラメータに依存した戻り値型がサポートされているか',
        default: false
      };
    }

    // 例
    if (feature.dependentFunctionTypes.examples) {
      schema.properties.dependentFunctionTypes.properties.examples = {
        type: 'array',
        items: {
          type: 'string'
        },
        description: '依存関数型の例'
      };
    }
  }

  // 証明関連
  if (feature.proofRelevance) {
    schema.properties.proofRelevance = {
      type: 'object',
      description: '証明関連機能',
      properties: {
        supported: {
          type: 'boolean',
          description: '証明関連機能がサポートされているか',
          default: false
        }
      }
    };

    // 消去可能性
    if (feature.proofRelevance.erasability !== undefined) {
      schema.properties.proofRelevance.properties.erasability = {
        type: 'boolean',
        description: '実行時に型が消去可能か',
        default: false
      };
    }

    // 抽出可能証明
    if (feature.proofRelevance.extractableProofs !== undefined) {
      schema.properties.proofRelevance.properties.extractableProofs = {
        type: 'boolean',
        description: '証明からプログラムの抽出が可能か',
        default: false
      };
    }

    // 保証付き計算
    if (feature.proofRelevance.certifiedComputation !== undefined) {
      schema.properties.proofRelevance.properties.certifiedComputation = {
        type: 'boolean',
        description: '保証付き計算がサポートされているか',
        default: false
      };
    }
  }

  return schema;
}

/**
 * 型システムのスキーマを生成する
 * 
 * @param feature 型システム機能特性オブジェクト
 * @returns 型システムスキーマ
 */
export function createTypeSystemSchema(feature?: TypeSystemFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: '型システムに関する詳細情報',
    properties: {}
  };

  // 型システムの種類
  if (feature.kind) {
    schema.properties.kind = {
      type: 'string',
      enum: ['static', 'dynamic', 'gradual', 'soft', 'hybrid'],
      description: '型システムの種類',
      default: 'static'
    };
  }

  // 代数的データ型
  const adtSchema = createAlgebraicDataTypeSchema(feature.algebraicDataTypes);
  if (adtSchema) {
    schema.properties.algebraicDataTypes = adtSchema;
  }

  // ジェネリック型
  const genericSchema = createGenericTypeSchema(feature.generics);
  if (genericSchema) {
    schema.properties.generics = genericSchema;
  }

  // 依存型
  const dependentSchema = createDependentTypeSchema(feature.dependentTypes);
  
  // 拡張依存型スキーマの生成
  let extendedDependentSchema = null;
  if (feature.dependentTypes) {
    // 依存型のサブ機能を取得
    const typeLevelProgramming: TypeLevelProgrammingFeature = {
      supported: !!feature.dependentTypes.typeLevelComputation?.supported,
      computation: {
        arithmetic: !!feature.dependentTypes.typeLevelComputation?.typeFunctions?.supported,
        stringManipulation: !!feature.dependentTypes.typeLevelComputation?.typeFunctions?.supported,
        listManipulation: !!feature.dependentTypes.typeLevelComputation?.typeFunctions?.supported,
        recursion: !!feature.dependentTypes.typeLevelComputation?.recursion
      },
      conditionals: feature.dependentTypes.typeLevelComputation?.conditionals ? {
        supported: !!feature.dependentTypes.typeLevelComputation.conditionals.supported,
        branches: !!feature.dependentTypes.typeLevelComputation.conditionals.ifThenElse,
        typeSelection: !!feature.dependentTypes.typeLevelComputation.conditionals.patternMatching
      } : undefined
    };
    
    const singletonType: SingletonTypeFeature = feature.dependentTypes.singletonTypes ? {
      supported: !!feature.dependentTypes.singletonTypes.supported,
      applicableTypes: feature.dependentTypes.singletonTypes.literalTypes?.map(t => t === 'number' ? 'numeric' : t).filter(t => 
        ['string', 'numeric', 'boolean', 'custom'].includes(t)) as any
    } : { supported: false };
    
    const refinementType: RefinementTypeFeature = feature.dependentTypes.refinementTypes ? {
      supported: !!feature.dependentTypes.refinementTypes.supported,
      verification: {
        static: !!feature.dependentTypes.refinementTypes.staticVerification,
        dynamic: !!feature.dependentTypes.refinementTypes.dynamicVerification
      }
    } : { supported: false };
    
    // 拡張依存型スキーマを生成
    extendedDependentSchema = createExtendedDependentTypeSchema(
      feature.dependentTypes,
      typeLevelProgramming,
      singletonType,
      refinementType
    );
  }
  
  // 依存型スキーマを設定（拡張版があればそちらを優先）
  if (extendedDependentSchema) {
    schema.properties.dependentTypes = extendedDependentSchema;
  } else if (dependentSchema) {
    schema.properties.dependentTypes = dependentSchema;
  }

  // 型推論
  if (feature.typeInference) {
    schema.properties.typeInference = {
      type: 'object',
      description: '型推論の特性',
      properties: {
        supported: {
          type: 'boolean',
          description: '型推論がサポートされているか',
          default: false
        }
      }
    };

    // アルゴリズム
    if (feature.typeInference.algorithm) {
      schema.properties.typeInference.properties.algorithm = {
        type: 'string',
        description: '型推論アルゴリズム'
      };
    }

    // 完全性
    if (feature.typeInference.completeness) {
      schema.properties.typeInference.properties.completeness = {
        type: 'string',
        enum: ['partial', 'complete'],
        description: '型推論の完全性',
        default: 'partial'
      };
    }

    // コンテキスト感度
    if (feature.typeInference.contextSensitive !== undefined) {
      schema.properties.typeInference.properties.contextSensitive = {
        type: 'boolean',
        description: 'コンテキスト感度のある型推論',
        default: false
      };
    }
  }

  // サブタイピング
  if (feature.subtyping) {
    schema.properties.subtyping = {
      type: 'object',
      description: 'サブタイピングの特性',
      properties: {
        supported: {
          type: 'boolean',
          description: 'サブタイピングがサポートされているか',
          default: false
        }
      }
    };

    // 構造的サブタイピング
    if (feature.subtyping.structural !== undefined) {
      schema.properties.subtyping.properties.structural = {
        type: 'boolean',
        description: '構造的サブタイピング',
        default: false
      };
    }

    // 名目的サブタイピング
    if (feature.subtyping.nominal !== undefined) {
      schema.properties.subtyping.properties.nominal = {
        type: 'boolean',
        description: '名目的サブタイピング',
        default: false
      };
    }

    // 変性
    if (feature.subtyping.variance !== undefined) {
      schema.properties.subtyping.properties.variance = {
        type: 'boolean',
        description: '変性のサポート',
        default: false
      };
    }
  }

  // 型の等価性
  if (feature.typeEquality) {
    schema.properties.typeEquality = {
      type: 'object',
      description: '型の等価性に関する特性',
      properties: {}
    };

    // 構造的等価性
    if (feature.typeEquality.structuralEquality !== undefined) {
      schema.properties.typeEquality.properties.structuralEquality = {
        type: 'boolean',
        description: '構造的型等価性',
        default: false
      };
    }

    // 名目的等価性
    if (feature.typeEquality.nominalEquality !== undefined) {
      schema.properties.typeEquality.properties.nominalEquality = {
        type: 'boolean',
        description: '名目的型等価性',
        default: false
      };
    }

    // 外延的等価性
    if (feature.typeEquality.extensionalEquality !== undefined) {
      schema.properties.typeEquality.properties.extensionalEquality = {
        type: 'boolean',
        description: '外延的型等価性',
        default: false
      };
    }
  }

  return schema;
}
