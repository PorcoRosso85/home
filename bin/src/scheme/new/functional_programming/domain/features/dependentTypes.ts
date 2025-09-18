/**
 * dependentTypes.ts
 * 
 * 依存型と型レベルプログラミングに関する機能特性のドメインモデル
 */

/**
 * 型レベルプログラミングの機能特性
 */
export interface TypeLevelProgrammingFeature {
  // 型レベルプログラミングのサポート
  supported: boolean;
  
  // 型レベル計算の特性
  computation?: {
    // 型レベルでの算術演算
    arithmetic?: boolean;
    // 型レベルでの文字列操作
    stringManipulation?: boolean;
    // 型レベルでのリスト/タプル操作
    listManipulation?: boolean;
    // 型レベルでの再帰
    recursion?: boolean;
  };
  
  // 型レベル条件分岐
  conditionals?: {
    supported: boolean;
    // 型レベルのif-thenなど
    branches?: boolean;
    // 型システム内での型選択
    typeSelection?: boolean;
  };
  
  // 型レベルでの検証と証明機能
  verification?: {
    supported: boolean;
    // 型安全性の証明
    typeSafetyProofs?: boolean;
    // 値に関する定理の証明
    valueTheorems?: boolean;
  };
  
  // メタプログラミング機能
  metaprogramming?: {
    supported: boolean;
    // コンパイル時コード生成
    codeGeneration?: boolean;
    // リフレクション機能
    reflection?: boolean;
    // 型からのインスタンス化
    instantiation?: boolean;
  };
}

/**
 * 依存型の機能特性
 */
export interface DependentTypeFeature {
  // 依存型のサポート
  supported: boolean;
  
  // 依存型の種類
  kinds?: {
    // 値に依存した型（Pi型）
    piTypes?: boolean;
    // 依存レコード型（Sigma型）
    sigmaTypes?: boolean;
    // 単一値を表す型（シングルトン型）
    singletonTypes?: boolean;
    // 値に基づき絞り込まれた型（リファインメント型）
    refinementTypes?: boolean;
  };
  
  // 依存型の表現方法
  representation?: Array<'function-parameters' | 'generic-parameters' | 'type-predicates' | 'custom'>;
  
  // 値と型の境界
  valueTypeInteraction?: {
    // 型から値への影響（型クラスなど）
    typeToValueFlow?: boolean;
    // 値から型への影響（依存型）
    valueToTypeFlow?: boolean;
    // 実行時型情報の利用
    runtimeTypeInfo?: boolean;
  };
  
  // コンパイル時と実行時の型チェック
  typeChecking?: {
    // 静的型チェック（コンパイル時）
    static?: boolean;
    // 動的型チェック（実行時）
    dynamic?: boolean;
    // ハイブリッド型チェック
    hybrid?: boolean;
  };
}

/**
 * シングルトン型の機能特性
 */
export interface SingletonTypeFeature {
  // シングルトン型のサポート
  supported: boolean;
  
  // 適用可能な型
  applicableTypes?: Array<'literal' | 'numeric' | 'string' | 'boolean' | 'object' | 'custom'>;
  
  // シングルトン型の用途
  usages?: {
    // 型レベルでの値の保持
    valuePreservation?: boolean;
    // 関数間での値の伝播
    valuePropagation?: boolean;
    // 型安全なキャスト
    typeSafeCasting?: boolean;
  };
}

/**
 * リファインメント型の機能特性
 */
export interface RefinementTypeFeature {
  // リファインメント型のサポート
  supported: boolean;
  
  // 述語式の形式
  predicateForm?: Array<'type-predicate' | 'type-guard' | 'assertion' | 'constraint' | 'custom'>;
  
  // 検証方法
  verification?: {
    // 静的検証（コンパイル時）
    static?: boolean;
    // 動的検証（実行時）
    dynamic?: boolean;
    // SMTソルバーの使用
    smtSolver?: boolean;
  };
  
  // リファインメント型の用途
  usages?: {
    // 境界チェック（範囲など）
    boundChecking?: boolean;
    // Nullチェック
    nullChecking?: boolean;
    // 整合性検証
    consistencyValidation?: boolean;
    // プロトコル適合性
    protocolConformance?: boolean;
  };
}
