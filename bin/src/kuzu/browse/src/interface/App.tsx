import React, { useState, useEffect } from 'react';
import TreeNode, { TreeNodeData } from './components/TreeNode';
import { fetchAndBuildTree } from '../application/dataFetcher';

// URIの配列からツリー構造を構築する関数（後方互換性のため残す）
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
  const [treeData, setTreeData] = useState<TreeNodeData[]>([]);
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // データ取得の副作用
  useEffect(() => {
    // データベースの初期化完了を待つ
    const handleDatabaseReady = async () => {
      try {
        console.log('✓ database-ready イベントを受信しました');
        setIsLoading(true);
        setError(null);
        console.log('✓ データ取得を開始します...');
        const data = await fetchAndBuildTree();
        console.log('✓ データ取得成功:', data);
        setTreeData(data);
      } catch (err) {
        console.error('✗ データ取得エラー:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load data';
        setError(errorMessage);
        console.error('詳細エラー情報:', {
          message: err.message,
          stack: err.stack,
          name: err.name
        });
      } finally {
        setIsLoading(false);
        console.log('✓ データ取得処理完了');
      }
    };

    // カスタムイベントでデータベース初期化の完了を待つ
    const eventName = 'database-ready';
    console.log(`✓ ${eventName} イベントリスナーを設定します`);
    document.addEventListener(eventName, handleDatabaseReady);

    // 初期状態でデータベースが準備済みの場合を考慮
    if (window.conn) {
      console.log('✓ データベースは既に準備済み、直接データを読み込みます');
      handleDatabaseReady();
    } else {
      console.log('✓ データベース初期化を待機中...');
    }

    // クリーンアップ
    return () => {
      console.log(`✓ ${eventName} イベントリスナーを削除します`);
      document.removeEventListener(eventName, handleDatabaseReady);
    };
  }, []);

  const handleNodeClick = (node: TreeNodeData) => {
    setSelectedNode(node);
    console.log('Selected node:', node);
  };

  // ローディング表示
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  // エラー表示
  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'Arial, sans-serif',
        color: 'red'
      }}>
        <div>Error: {error}</div>
      </div>
    );
  }

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ flex: 1, overflowY: 'auto', marginRight: '20px' }}>
        <h2>KuzuDB Graph Browser</h2>
        {treeData.length === 0 ? (
          <p>No data available</p>
        ) : (
          treeData.map((node, index) => (
            <TreeNode
              key={`root-${index}`}
              node={node}
              onNodeClick={handleNodeClick}
            />
          ))
        )}
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
  );
};

export default App;