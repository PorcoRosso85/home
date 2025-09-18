/**
 * treeNode.ts
 * 
 * ツリー構造のドメインモデル
 */

import { FunctionSchema } from '/home/nixos/scheme/new/functional_programming/domain/schema.ts';

/**
 * ツリーノード型定義
 */
export interface TreeNode {
  name: string;
  type?: 'function' | 'folder';
  schema?: FunctionSchema;
  children: Record<string, TreeNode>;
}
