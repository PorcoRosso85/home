/**
 * typeSystem.ts
 * 
 * 型システムに関する機能特性のドメインモデル
 */

/**
 * 代数的データ型（ADT）の特性
 */
export interface AlgebraicDataTypeFeature {
  // サム型（直和型）の特性
  sumTypes?: {
    supported: boolean;
    representation?: 'tagged-union' | 'variant-record' | 'polymorphic-variant' | 'custom';
    examples?: string[];
  };

  // プロダクト型（直積型）の特性
  productTypes?: {
    supported: boolean;
    representation?: 'tuple' | 'record' | 'class' | 'custom';
    examples?: string[];
  };

  // パターンマッチングの特性
  patternMatching?: {
    supported: boolean;
    exhaustivenessChecking?: boolean; // 網羅性チェック
    nestedPatterns?: boolean;        // ネストされたパターン
    guardExpressions?: boolean;      // ガード式
  };
}

/**
 * ジェネリック型の特性
 */
export interface GenericTypeFeature {
  // ジェネリック型のサポート
  supported: boolean;
  
  // 型パラメータの特性
  typeParameters?: {
    variance?: 'invariant' | 'covariant' | 'contravariant' | 'bivariant';
    constraints?: {
      supported: boolean;
      constraintMechanisms?: Array<'subtyping' | 'typeclasses' | 'interfaces' | 'concepts' | 'custom'>;
    };
  };
  
  // 高階型のサポート
  higherKindedTypes?: {
    supported: boolean;
    maxKindLevel?: number;
    examples?: string[];
  };
}

/**
 * 依存型の特性
 */
export interface DependentTypeFeature {
  // 依存型のサポート
  supported: boolean;
  
  // 値による型のインデックス化
  valueIndexing?: {
    supported: boolean;
    expressionRestrictions?: string;
    // 型が依存できる値の種類
    allowedValueTypes?: Array<'constant' | 'parameter' | 'computed' | 'global'>;
    // 型依存の方向性
    dependencyDirection?: 'value-to-type' | 'type-to-value' | 'bidirectional';
  };
  
  // 洗練型のサポート
  refinementTypes?: {
    supported: boolean;
    staticVerification?: boolean;
    dynamicVerification?: boolean;
    expressionComplexity?: 'simple' | 'moderate' | 'complex';
    predicateLanguage?: string; // 述語言語の説明（SMT, FOL, HOL, etc.）
    examplePredicates?: string[]; // 述語の例
  };
  
  // 型レベル計算
  typeLevelComputation?: {
    supported: boolean;
    recursion?: boolean;
    examples?: string[];
    // 型レベル関数サポート
    typeFunctions?: {
      supported: boolean;
      higherOrder?: boolean; // 高階関数サポート
      recursiveDefinitions?: boolean; // 再帰的な型関数定義
      applicationSyntax?: string; // 型適用の構文例
    };
    // 型レベル条件分岐
    conditionals?: {
      supported: boolean;
      ifThenElse?: boolean;
      patternMatching?: boolean;
      guardedTypes?: boolean;
    };
  };
  
  // シングルトン型
  singletonTypes?: {
    supported: boolean;
    literalTypes?: Array<'number' | 'string' | 'boolean' | 'symbol' | 'custom'>;
    promotedValues?: boolean; // 値の型レベルへの昇格
  };
  
  // 依存関数型
  dependentFunctionTypes?: {
    supported: boolean;
    piTypes?: boolean; // Pi型のサポート
    dependentParameters?: boolean; // パラメータに依存した戻り値型
    examples?: string[];
  };
  
  // 証明関連
  proofRelevance?: {
    supported: boolean;
    erasability?: boolean; // 実行時に型が消去可能か
    extractableProofs?: boolean; // 証明から計算プログラムの抽出
    certifiedComputation?: boolean; // 保証付き計算
  };
}

/**
 * 型レベルプログラミング機能
 */
export interface TypeLevelProgrammingFeature {
  // 型レベルプログラミングのサポート
  supported: boolean;
  
  // 型レベルリテラル
  typeLevelLiterals?: {
    numbers?: boolean;
    strings?: boolean;
    booleans?: boolean;
    custom?: string[]; // カスタムリテラル型
  };
  
  // 型レベル演算子
  typeLevelOperators?: {
    logical?: Array<'and' | 'or' | 'not' | 'implies'>;
    arithmetic?: Array<'add' | 'subtract' | 'multiply' | 'divide' | 'mod'>;
    comparison?: Array<'equals' | 'lessThan' | 'greaterThan'>;
    string?: Array<'concat' | 'length' | 'substring'>;
    structural?: Array<'merge' | 'extract' | 'exclude' | 'pick'>;
  };
  
  // 型レベル制御構造
  typeLevelControlFlow?: {
    conditionals?: boolean;
    iteration?: boolean;
    recursion?: boolean;
    patternMatching?: boolean;
  };
  
  // 型レベルデータ構造
  typeLevelDataStructures?: {
    lists?: boolean;
    tuples?: boolean;
    records?: boolean;
    maps?: boolean;
    sets?: boolean;
    customStructures?: string[];
  };
  
  // メタプログラミング機能
  metaprogramming?: {
    templateTypes?: boolean; // テンプレートメタプログラミング
    introspection?: boolean; // 型の内省
    codeGeneration?: boolean; // コード生成
    macros?: boolean; // マクロシステム
  };
  
  // 型の推論可能性
  inferability?: {
    fullyInferable?: boolean;
    requiresAnnotations?: Array<'functions' | 'higherOrder' | 'recursion' | 'polymorphic'>;
    inferenceAlgorithm?: string;
  };
  
  // 実用的側面
  practicality?: {
    developerExperience?: 'simple' | 'moderate' | 'complex';
    errorMessages?: 'basic' | 'detailed' | 'guided';
    compileTimeImpact?: 'minimal' | 'moderate' | 'significant';
    toolingSupport?: boolean;
  };
}

/**
 * 型システムの機能特性
 */
export interface TypeSystemFeature {
  // 型システムの種類
  kind?: 'static' | 'dynamic' | 'gradual' | 'soft' | 'hybrid';
  
  // 代数的データ型
  algebraicDataTypes?: AlgebraicDataTypeFeature;
  
  // ジェネリック型
  generics?: GenericTypeFeature;
  
  // 依存型
  dependentTypes?: DependentTypeFeature;
  
  // 型レベルプログラミング
  typeLevelProgramming?: TypeLevelProgrammingFeature;
  
  // 型推論
  typeInference?: {
    supported: boolean;
    algorithm?: string;
    completeness?: 'partial' | 'complete';
    contextSensitive?: boolean;
  };
  
  // サブタイピング
  subtyping?: {
    supported: boolean;
    structural?: boolean;
    nominal?: boolean;
    variance?: boolean;
  };
  
  // 型の等価性
  typeEquality?: {
    structuralEquality?: boolean;
    nominalEquality?: boolean;
    extensionalEquality?: boolean;
  };
}
