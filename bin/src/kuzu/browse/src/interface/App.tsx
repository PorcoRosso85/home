import React, { useState } from 'react';
import TreeNode, { TreeNodeData } from './components/TreeNode';
import MinimalRpcButton from '../../rpc/components/MinimalRpcButton';

// FIXME: ダミーデータをグラフデータへ移行
const dummyUris = [
  '/nodes/person/1/knows/person/2',
  '/nodes/person/1/lives_in/city/3',
  '/nodes/person/2/works_at/company/4',
  '/nodes/person/1/friend_of/person/5',
  '/nodes/person/5/owns/product/6',
  '/nodes/company/4/located_in/city/3'
];

// URIの配列からツリー構造を構築する関数
const buildTreeFromUris = (uris: string[]): TreeNodeData[] => {
  const treeMap: Record<string, TreeNodeData> = {};
  const rootNodes: TreeNodeData[] = [];

  uris.forEach((uri, index) => {
    const segments = uri.split('/').filter(segment => segment.length > 0);
    
    let currentPath = '';
    let parentNode: TreeNodeData | null = null;
    
    segments.forEach((segment, i) => {
      const isLeaf = i === segments.length - 1;
      const segmentPath = currentPath + '/' + segment;
      currentPath = segmentPath;
      
      if (!treeMap[segmentPath]) {
        // 新しいノードを作成
        const newNode: TreeNodeData = {
          id: `node-${index}-${i}`,
          type: i % 2 === 0 ? 'entity' : 'value',
          name: segment,
          uri: segmentPath,
          properties: { 
            path: segmentPath,
            isLeaf
          },
          children: []
        };
        
        treeMap[segmentPath] = newNode;
        
        if (parentNode) {
          // 親ノードに追加
          parentNode.children?.push(newNode);
        } else if (i === 0) {
          // ルートノードの場合
          rootNodes.push(newNode);
        }
      }
      
      parentNode = treeMap[segmentPath];
    });
  });
  
  return rootNodes;
};

const App = () => {
  const [treeData, setTreeData] = useState<TreeNodeData[]>(buildTreeFromUris(dummyUris));
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);

  const handleNodeClick = (node: TreeNodeData) => {
    setSelectedNode(node);
    console.log('Selected node:', node);
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100vh', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        marginBottom: '20px',
        padding: '10px',
        backgroundColor: '#f0f0f0',
        borderRadius: '8px'
      }}>
        <h2 style={{ margin: '0' }}>KuzuDB Graph Browser</h2>
        <MinimalRpcButton />
      </div>
      
      <div style={{ display: 'flex', flex: 1, overflowY: 'auto' }}>
        <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
          {treeData.map((node, index) => (
            <TreeNode
              key={`root-${index}`}
              node={node}
              onNodeClick={handleNodeClick}
            />
          ))}
        </div>
        
        {selectedNode && (
          <div style={{ 
            flex: 1, 
            padding: '15px',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h3>Node Details</h3>
            <div>
              <p><strong>ID:</strong> {selectedNode.id}</p>
              <p><strong>Type:</strong> {selectedNode.type}</p>
              <p><strong>Name:</strong> {selectedNode.name}</p>
              <p><strong>URI:</strong> {selectedNode.uri}</p>
              <h4>Properties:</h4>
              <pre style={{ 
                backgroundColor: '#e8e8e8', 
                padding: '10px', 
                borderRadius: '4px' 
              }}>
                {JSON.stringify(selectedNode.properties, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
