// App.tsx - メインアプリケーションコンポーネント
import React, { useEffect, useState } from "https://esm.sh/react@18.2.0";
import { GraphData, Node, Edge } from "./types/types";
import GraphViewer from "./components/GraphViewer";
import NodeDetail from "./components/NodeDetail";

const App: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [relatedEdges, setRelatedEdges] = useState<Edge[]>([]);
  
  // 初期データ読み込み
  useEffect(() => {
    const loadGraphData = async () => {
      try {
        setLoading(true);
        
        // データを取得
        const [nodesResponse, edgesResponse, subgraphsResponse, metadataResponse] = await Promise.all([
          fetch('./db/nodes.json'),
          fetch('./db/edges.json'),
          fetch('./db/subgraphs.json'),
          fetch('./db/metadata.json')
        ]);
        
        if (!nodesResponse.ok || !edgesResponse.ok || !subgraphsResponse.ok || !metadataResponse.ok) {
          throw new Error('JSONデータの取得に失敗しました');
        }
        
        // JSONデータをパース
        const nodes = await nodesResponse.json();
        const edges = await edgesResponse.json();
        const subgraphs = await subgraphsResponse.json();
        const metadata = await metadataResponse.json();
        
        // グラフデータを設定
        setGraphData({
          nodes,
          edges,
          subgraphs,
          metadata
        });
        
        setError(null);
      } catch (err) {
        console.error('グラフデータの読み込みに失敗しました:', err);
        setError('データの読み込みに失敗しました。再読み込みを試してください。');
      } finally {
        setLoading(false);
      }
    };
    
    loadGraphData();
  }, []);
  
  // ノード選択時の処理
  useEffect(() => {
    if (!selectedNodeId || !graphData) {
      setSelectedNode(null);
      setRelatedEdges([]);
      return;
    }
    
    const node = graphData.nodes[selectedNodeId];
    if (node) {
      setSelectedNode(node);
      
      // 関連するエッジを抽出
      const edges = graphData.edges.filter(
        edge => edge.source === selectedNodeId || edge.target === selectedNodeId
      );
      
      setRelatedEdges(edges);
    } else {
      setSelectedNode(null);
      setRelatedEdges([]);
    }
  }, [selectedNodeId, graphData]);
  
  // ノード詳細パネルを閉じる
  const closeNodeDetail = () => {
    setSelectedNodeId(null);
  };
  
  // ローディング表示
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh', 
        flexDirection: 'column' 
      }}>
        <div style={{ 
          width: '48px', 
          height: '48px', 
          border: '4px solid #e5e7eb', 
          borderTop: '4px solid #3b82f6', 
          borderRadius: '50%', 
          animation: 'spin 1s linear infinite' 
        }}></div>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
        <p style={{ marginTop: '16px', color: '#4b5563' }}>データを読み込んでいます...</p>
      </div>
    );
  }
  
  // エラー表示
  if (error && !graphData) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh' 
      }}>
        <div style={{
          backgroundColor: '#fee2e2',
          border: '1px solid #ef4444',
          color: '#b91c1c',
          padding: '16px',
          borderRadius: '8px',
          maxWidth: '400px',
          textAlign: 'center'
        }}>
          <h2 style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '8px' }}>エラーが発生しました</h2>
          <p>{error}</p>
          <button
            style={{
              marginTop: '16px',
              backgroundColor: '#ef4444',
              color: 'white',
              fontWeight: 'bold',
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer'
            }}
            onClick={() => window.location.reload()}
          >
            再読み込み
          </button>
        </div>
      </div>
    );
  }
  
  // メインのUI
  return (
    <div style={{ width: "100%", height: "100vh", overflow: "hidden" }}>
      {/* グラフビューア（画面全体に表示） */}
      {graphData && (
        <GraphViewer graphData={graphData} onNodeSelect={setSelectedNodeId} />
      )}

      {/* ノード詳細パネル (選択時のみ表示) */}
      {selectedNode && (
        <NodeDetail 
          node={selectedNode} 
          relatedEdges={relatedEdges} 
          onClose={closeNodeDetail} 
        />
      )}
    </div>
  );
};

export default App;
