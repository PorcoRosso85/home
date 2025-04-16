/**
 * detailView.ts
 * 
 * 詳細表示コンポーネント
 */

import { TreeNode } from '../../domain/models/treeNode.ts';
import { Graph } from '/home/nixos/scheme/new/functional_programming/domain/entities/graph.ts';

/**
 * 依存関係ビューの更新
 */
export function renderDetailView(container: HTMLElement, node: TreeNode, graphData?: Graph): void {
  if (!container) return;
  
  // スキーマ情報の表示
  if (node.schema) {
    container.innerHTML = `
      <div class="schema-info">
        <h2>${node.schema.title}</h2>
        <p>${node.schema.description || '説明なし'}</p>
        
        <h3>スキーマ情報</h3>
        <table>
          <tr><th>タイプ</th><td>${node.schema.type}</td></tr>
          <tr><th>リソースURI</th><td>${node.schema.resourceUri || 'なし'}</td></tr>
        </table>
        
        <h3>プロパティ</h3>
        <pre>${JSON.stringify(node.schema.properties, null, 2)}</pre>
      </div>
    `;
    
    // 依存関係がある場合は表示
    if (graphData) {
      const nodeId = node.schema.title;
      const edges = graphData.edges.filter(edge => 
        edge.source === nodeId || edge.target === nodeId
      );
      
      if (edges.length > 0) {
        const edgesHtml = edges.map(edge => {
          const isSource = edge.source === nodeId;
          const direction = isSource ? '→' : '←';
          const otherNode = isSource ? edge.target : edge.source;
          const edgeClass = edge.properties.isCircular ? 'circular' : '';
          
          return `
            <tr class="${edgeClass}">
              <td>${isSource ? nodeId : otherNode}</td>
              <td>${direction}</td>
              <td>${isSource ? otherNode : nodeId}</td>
              <td>${edge.label}</td>
            </tr>
          `;
        }).join('');
        
        container.innerHTML += `
          <div class="dependencies">
            <h3>依存関係</h3>
            <table class="edges-table">
              <tr>
                <th>ソース</th>
                <th></th>
                <th>ターゲット</th>
                <th>タイプ</th>
              </tr>
              ${edgesHtml}
            </table>
          </div>
        `;
      }
    }
  } else {
    container.innerHTML = '<div class="message">ノードを選択してください</div>';
  }
}
