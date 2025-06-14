/**
 * schema.ts
 * 
 * 関数型プログラミングのためのスキーマのドメインモデル
 */

import { FunctionFeatures } from './features/index.ts';

/**
 * 基本的なスキーマ構造
 */
export interface FunctionSchema {
  $schema: string;
  title: string;
  description: string;
  type: string;
  required: string[];
  resourceUri?: string;
  properties: Record<string, any>;
}

// 型のみをエクスポート
export type { FunctionFeatures };
