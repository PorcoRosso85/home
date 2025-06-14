/**
 * index.ts
 * 
 * 機能特性ドメインモデルのインデックスファイル
 */

import { createPurityFeatureSchema, PurityFeature } from './purityFeature.ts';
import { createEvaluationFeatureSchema, EvaluationFeature } from './evaluationFeature.ts';
import { createCurryingFeatureSchema, CurryingFeature } from './curryingFeature.ts';
import { createRecursionFeatureSchema, RecursionFeature } from './recursionFeature.ts';
import { 
  TypeSystemFeature,
  AlgebraicDataTypeFeature, 
  GenericTypeFeature, 
  DependentTypeFeature 
} from './typeSystem.ts';
import {
  TypeLevelProgrammingFeature,
  SingletonTypeFeature,
  RefinementTypeFeature
} from './dependentTypes.ts';
import { CompositionFeature } from './composition.ts';
import { TestsFeature } from './tests/index.ts';

/**
 * すべての関数特性の集合
 */
export interface FunctionFeatures {
  purity?: PurityFeature;
  evaluation?: EvaluationFeature;
  currying?: CurryingFeature;
  recursion?: RecursionFeature;
  memoization?: any;
  async?: any;
  multipleReturns?: any;
  typeSystem?: TypeSystemFeature;
  composition?: CompositionFeature;
  tests?: TestsFeature;
}

// 型のみをエクスポート
export type { PurityFeature };
export type { EvaluationFeature };
export type { CurryingFeature };
export type { RecursionFeature };
export type { TypeSystemFeature };
export type { AlgebraicDataTypeFeature, GenericTypeFeature, DependentTypeFeature };
export type { TypeLevelProgrammingFeature, SingletonTypeFeature, RefinementTypeFeature };
export type { CompositionFeature };
export type { TestsFeature };

// 関数のエクスポート
export {
  createPurityFeatureSchema,
  createEvaluationFeatureSchema,
  createCurryingFeatureSchema,
  createRecursionFeatureSchema
};
