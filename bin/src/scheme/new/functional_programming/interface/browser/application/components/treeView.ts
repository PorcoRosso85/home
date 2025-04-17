/**
 * treeView.ts
 * 
 * ツリービューコンポーネント
 */

import { TreeNode } from '../../domain/models/treeNode.ts';

/**
 * ツリーを再帰的にレンダリング
 * @param container 対象のDOM要素
 * @param node ツリーノード
 * @param onNodeSelect ノード選択時のコールバック
 */
export function renderTree(container: HTMLElement, node: TreeNode, onNodeSelect: (node: TreeNode) => void): void {
  container.innerHTML = '';
  const rootUl = document.createElement('ul');
  rootUl.className = 'tree';
  container.appendChild(rootUl);
  
  // ルートの子要素をレンダリング
  const children = Object.values(node.children);
  for (const child of children) {
    renderTreeNode(rootUl, child, 1, onNodeSelect);
  }
}

/**
 * ツリーノードのレンダリング
 */
function renderTreeNode(
  parentEl: HTMLElement, 
  node: TreeNode, 
  level: number, 
  onNodeSelect: (node: TreeNode) => void
): void {
  const li = document.createElement('li');
  
  // フォルダ/ファイルアイコン
  const hasChildren = Object.keys(node.children).length > 0;
  const icon = hasChildren ? '📁' : (node.type === 'function' ? '📄' : '📄');
  
  const nodeSpan = document.createElement('span');
  nodeSpan.className = `tree-node ${node.type || 'folder'}`;
  nodeSpan.innerHTML = `${icon} ${node.name}`;
  
  // クリックイベント
  nodeSpan.addEventListener('click', () => {
    if (node.type === 'function') {
      onNodeSelect(node);
    } else if (hasChildren) {
      // フォルダの開閉
      const childrenUl = li.querySelector('ul');
      if (childrenUl) {
        childrenUl.style.display = childrenUl.style.display === 'none' ? 'block' : 'none';
        nodeSpan.innerHTML = `${childrenUl.style.display === 'none' ? '📁' : '📂'} ${node.name}`;
      }
    }
  });
  
  li.appendChild(nodeSpan);
  
  // 子要素があれば再帰的にレンダリング
  if (hasChildren) {
    const childrenUl = document.createElement('ul');
    li.appendChild(childrenUl);
    
    const children = Object.values(node.children);
    for (const child of children) {
      renderTreeNode(childrenUl, child, level + 1, onNodeSelect);
    }
  }
  
  parentEl.appendChild(li);
}
