/**
 * dependentTypeSchema.ts
 * 
 * 依存型と型レベルプログラミングのスキーマを生成する関数
 */

import { 
  DependentTypeFeature 
} from '../../domain/features/typeSystem.ts';
import {
  TypeLevelProgrammingFeature,
  SingletonTypeFeature,
  RefinementTypeFeature
} from '../../domain/features/dependentTypes.ts';

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
    },
    required: ['supported']
  };

  // 値による型のインデックス化
  if (feature.valueIndexing) {
    schema.properties.valueIndexing = {
      type: 'object',
      description: '値による型のインデックス化',
      properties: {
        supported: {
          type: 'boolean',
          description: '値によるインデックス化がサポートされているか',
          default: false
        }
      },
      required: ['supported']
    };

    if (feature.valueIndexing.expressionRestrictions) {
      schema.properties.valueIndexing.properties.expressionRestrictions = {
        type: 'string',
        description: '式の制限'
      };
    }

    if (feature.valueIndexing.allowedValueTypes) {
      schema.properties.valueIndexing.properties.allowedValueTypes = {
        type: 'array',
        description: '型が依存できる値の種類',
        items: {
          type: 'string',
          enum: ['constant', 'parameter', 'computed', 'global']
        }
      };
    }

    if (feature.valueIndexing.dependencyDirection) {
      schema.properties.valueIndexing.properties.dependencyDirection = {
        type: 'string',
        description: '型依存の方向性',
        enum: ['value-to-type', 'type-to-value', 'bidirectional']
      };
    }
  }

  // リファインメント型のサポート
  if (feature.refinementTypes) {
    schema.properties.refinementTypes = {
      type: 'object',
      description: 'リファインメント型のサポート',
      properties: {
        supported: {
          type: 'boolean',
          description: 'リファインメント型がサポートされているか',
          default: false
        }
      },
      required: ['supported']
    };

    if (feature.refinementTypes.staticVerification !== undefined) {
      schema.properties.refinementTypes.properties.staticVerification = {
        type: 'boolean',
        description: '静的検証のサポート'
      };
    }

    if (feature.refinementTypes.dynamicVerification !== undefined) {
      schema.properties.refinementTypes.properties.dynamicVerification = {
        type: 'boolean',
        description: '動的検証のサポート'
      };
    }

    if (feature.refinementTypes.expressionComplexity) {
      schema.properties.refinementTypes.properties.expressionComplexity = {
        type: 'string',
        description: '式の複雑さ',
        enum: ['simple', 'moderate', 'complex']
      };
    }

    if (feature.refinementTypes.predicateLanguage) {
      schema.properties.refinementTypes.properties.predicateLanguage = {
        type: 'string',
        description: '述語言語の説明'
      };
    }
  }

  return schema;
}

/**
 * 型レベルプログラミングのスキーマを生成する
 * 
 * @param feature 型レベルプログラミング機能特性オブジェクト
 * @returns 型レベルプログラミングスキーマ
 */
export function createTypeLevelProgrammingSchema(feature?: TypeLevelProgrammingFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: '型レベルプログラミングのサポート情報',
    properties: {
      supported: {
        type: 'boolean',
        description: '型レベルプログラミングがサポートされているか',
        default: false
      }
    },
    required: ['supported']
  };

  // 型レベル計算のスキーマ
  if (feature.computation) {
    schema.properties.computation = {
      type: 'object',
      description: '型レベル計算の特性',
      properties: {
        arithmetic: {
          type: 'boolean',
          description: '型レベルでの算術演算のサポート',
          default: false
        },
        stringManipulation: {
          type: 'boolean',
          description: '型レベルでの文字列操作のサポート',
          default: false
        },
        listManipulation: {
          type: 'boolean',
          description: '型レベルでのリスト/タプル操作のサポート',
          default: false
        },
        recursion: {
          type: 'boolean',
          description: '型レベルでの再帰のサポート',
          default: false
        }
      }
    };
  }

  // 型レベル条件分岐のスキーマ
  if (feature.conditionals) {
    schema.properties.conditionals = {
      type: 'object',
      description: '型レベル条件分岐の特性',
      properties: {
        supported: {
          type: 'boolean',
          description: '型レベル条件分岐がサポートされているか',
          default: false
        },
        branches: {
          type: 'boolean',
          description: '型レベルのif-thenなどの条件分岐構造のサポート',
          default: false
        },
        typeSelection: {
          type: 'boolean',
          description: '型システム内での型選択機能のサポート',
          default: false
        }
      },
      required: ['supported']
    };
  }

  // 型レベル検証と証明のスキーマ
  if (feature.verification) {
    schema.properties.verification = {
      type: 'object',
      description: '型レベルでの検証と証明機能',
      properties: {
        supported: {
          type: 'boolean',
          description: '型レベル検証がサポートされているか',
          default: false
        },
        typeSafetyProofs: {
          type: 'boolean',
          description: '型安全性の証明機能',
          default: false
        },
        valueTheorems: {
          type: 'boolean',
          description: '値に関する定理の証明機能',
          default: false
        }
      },
      required: ['supported']
    };
  }

  // メタプログラミング機能のスキーマ
  if (feature.metaprogramming) {
    schema.properties.metaprogramming = {
      type: 'object',
      description: 'メタプログラミング機能',
      properties: {
        supported: {
          type: 'boolean',
          description: 'メタプログラミング機能がサポートされているか',
          default: false
        },
        codeGeneration: {
          type: 'boolean',
          description: 'コンパイル時コード生成機能',
          default: false
        },
        reflection: {
          type: 'boolean',
          description: 'リフレクション機能',
          default: false
        },
        instantiation: {
          type: 'boolean',
          description: '型からのインスタンス化機能',
          default: false
        }
      },
      required: ['supported']
    };
  }

  return schema;
}

/**
 * シングルトン型のスキーマを生成する
 * 
 * @param feature シングルトン型機能特性オブジェクト
 * @returns シングルトン型スキーマ
 */
export function createSingletonTypeSchema(feature?: SingletonTypeFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: 'シングルトン型のサポート情報',
    properties: {
      supported: {
        type: 'boolean',
        description: 'シングルトン型がサポートされているか',
        default: false
      }
    },
    required: ['supported']
  };

  // 適用可能な型のスキーマ
  if (feature.applicableTypes) {
    schema.properties.applicableTypes = {
      type: 'array',
      description: 'シングルトン型が適用可能な型',
      items: {
        type: 'string',
        enum: ['literal', 'numeric', 'string', 'boolean', 'object', 'custom']
      }
    };
  }

  // シングルトン型の用途のスキーマ
  if (feature.usages) {
    schema.properties.usages = {
      type: 'object',
      description: 'シングルトン型の用途',
      properties: {
        valuePreservation: {
          type: 'boolean',
          description: '型レベルでの値の保持',
          default: false
        },
        valuePropagation: {
          type: 'boolean',
          description: '関数間での値の伝播',
          default: false
        },
        typeSafeCasting: {
          type: 'boolean',
          description: '型安全なキャスト',
          default: false
        }
      }
    };
  }

  return schema;
}

/**
 * リファインメント型のスキーマを生成する
 * 
 * @param feature リファインメント型機能特性オブジェクト
 * @returns リファインメント型スキーマ
 */
export function createRefinementTypeSchema(feature?: RefinementTypeFeature): any {
  if (!feature) {
    return null;
  }

  const schema: any = {
    type: 'object',
    description: 'リファインメント型のサポート情報',
    properties: {
      supported: {
        type: 'boolean',
        description: 'リファインメント型がサポートされているか',
        default: false
      }
    },
    required: ['supported']
  };

  // 述語式の形式のスキーマ
  if (feature.predicateForm) {
    schema.properties.predicateForm = {
      type: 'array',
      description: '述語式の形式',
      items: {
        type: 'string',
        enum: ['type-predicate', 'type-guard', 'assertion', 'constraint', 'custom']
      }
    };
  }

  // 検証方法のスキーマ
  if (feature.verification) {
    schema.properties.verification = {
      type: 'object',
      description: 'リファインメント型の検証方法',
      properties: {
        static: {
          type: 'boolean',
          description: '静的検証（コンパイル時）',
          default: false
        },
        dynamic: {
          type: 'boolean',
          description: '動的検証（実行時）',
          default: false
        },
        smtSolver: {
          type: 'boolean',
          description: 'SMTソルバーの使用',
          default: false
        }
      }
    };
  }

  // リファインメント型の用途のスキーマ
  if (feature.usages) {
    schema.properties.usages = {
      type: 'object',
      description: 'リファインメント型の用途',
      properties: {
        boundChecking: {
          type: 'boolean',
          description: '境界チェック（範囲など）',
          default: false
        },
        nullChecking: {
          type: 'boolean',
          description: 'Nullチェック',
          default: false
        },
        consistencyValidation: {
          type: 'boolean',
          description: '整合性検証',
          default: false
        },
        protocolConformance: {
          type: 'boolean',
          description: 'プロトコル適合性',
          default: false
        }
      }
    };
  }

  return schema;
}

/**
 * 拡張依存型スキーマを生成する
 * 
 * 型レベルプログラミング、シングルトン型、リファインメント型などの
 * 詳細情報を含む統合された依存型スキーマを生成します。
 * 
 * @param dependentType 依存型機能特性
 * @param typeLevelProgramming 型レベルプログラミング機能特性
 * @param singletonType シングルトン型機能特性
 * @param refinementType リファインメント型機能特性
 * @returns 拡張依存型スキーマ
 */
export function createExtendedDependentTypeSchema(
  dependentType?: DependentTypeFeature,
  typeLevelProgramming?: TypeLevelProgrammingFeature,
  singletonType?: SingletonTypeFeature,
  refinementType?: RefinementTypeFeature
): any {
  const schema: any = {
    type: 'object',
    description: '拡張された依存型システムのサポート情報',
    properties: {}
  };

  // 各スキーマを生成
  const dependentTypeSchema = createDependentTypeSchema(dependentType);
  const typeLevelProgrammingSchema = createTypeLevelProgrammingSchema(typeLevelProgramming);
  const singletonTypeSchema = createSingletonTypeSchema(singletonType);
  const refinementTypeSchema = createRefinementTypeSchema(refinementType);

  // 依存型のスキーマを設定
  if (dependentTypeSchema) {
    schema.properties.dependentTypes = dependentTypeSchema;
  }

  // 型レベルプログラミングのスキーマを設定
  if (typeLevelProgrammingSchema) {
    schema.properties.typeLevelProgramming = typeLevelProgrammingSchema;
  }

  // シングルトン型のスキーマを設定
  if (singletonTypeSchema) {
    schema.properties.singletonTypes = singletonTypeSchema;
  }

  // リファインメント型のスキーマを設定
  if (refinementTypeSchema) {
    schema.properties.refinementTypes = refinementTypeSchema;
  }

  return schema;
}
