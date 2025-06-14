/**
 * 関数合成に関する機能定義
 */

export type CompositionPattern = 
  | 'pipeline'   // 関数を順次適用するパイプライン
  | 'pointfree'  // 引数を明示しない点無し記法
  | 'monad'      // モナド変換やバインド操作
  | 'applicative' // 適用的関手による合成
  | 'arrow'      // アロー（関数と合成操作の抽象）
  | 'lens'       // レンズパターン（getter/setter）
  | 'transducer'; // 変換器（効率的なデータ変換パイプライン）

export interface TransformationStage {
  stage: string;
  description: string;
  dependencies: string[];
}

export interface OutputAdaptation {
  pattern: string;
  description: string;
}

export interface OptimizationHints {
  fusable: boolean;        // 隣接関数の融合最適化が可能
  parallelizable: boolean; // 並列実行が可能
  memoizable: boolean;     // 結果のキャッシュが有効
  notes?: string;          // 追加の最適化情報
}

export interface DataFlowInfo {
  inputTransformations: TransformationStage[];
  outputAdaptations: OutputAdaptation[];
}

export interface CompositionFeature {
  composable: boolean;  // 他の関数と簡単に合成可能か
  compositionPatterns: CompositionPattern[];
  dataFlow: DataFlowInfo;
  optimizationHints: OptimizationHints;
}
