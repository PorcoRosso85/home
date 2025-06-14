/**
 * treeService.ts
 * 
 * ツリー構造に関するドメインサービス
 */

import { FunctionSchema } from '/home/nixos/scheme/new/functional_programming/domain/schema.ts';
import { TreeNode } from '../models/treeNode.ts';

/**
 * 関数データからツリー構造を構築
 */
export function buildTreeFromFunctionData(schemas: FunctionSchema[]): TreeNode {
  const root: TreeNode = {
    name: 'スキーマ',
    children: {}
  };
  
  // スキーマをパスで整理
  for (const schema of schemas) {
    const resourceUri = schema.resourceUri || '';
    const path = resourceUri.replace('file:///', '').split('/');
    
    // ファイル名を最後の要素として取得
    const fileName = path.pop() || schema.title;
    
    // パスに基づいてツリーを構築
    let current = root;
    for (const folder of path) {
      if (!folder) continue;
      
      if (!current.children[folder]) {
        current.children[folder] = {
          name: folder,
          type: 'folder',
          children: {}
        };
      }
      
      current = current.children[folder];
    }
    
    // リーフノード（関数）を追加
    current.children[fileName] = {
      name: fileName,
      type: 'function',
      schema,
      children: {}
    };
  }
  
  return root;
}
