// index.tsx - 上辺と左辺だけのボーダーを持つツリーコンポーネント
import React from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";

// NodeDataの型定義
interface NodeData {
  id: string;
  name: string;
  children?: NodeData[];
}

// ノードとエッジのデータ
const graphData = {
  nodes: [
    { id: 'root', name: 'python_project' },
    { id: 'child1', name: 'models' },
    { id: 'child2', name: 'utils' },
    { id: 'grandchild1', name: 'user_model.py' },
    { id: 'grandchild2', name: 'product_model.py' },
    { id: 'grandchild3', name: 'helpers.py' },
    { id: 'great-grandchild1', name: 'def validate_user()' },
    { id: 'great-grandchild2', name: 'def save_user()' },
    { id: 'great-grandchild3', name: 'def get_product()' },
    { id: 'great-grandchild4', name: 'def format_data()' },
    { id: 'great-grandchild5', name: 'def parse_input()' }
  ],
  edges: [
    { from: 'root', to: 'child1' },
    { from: 'root', to: 'child2' },
    { from: 'child1', to: 'grandchild1' },
    { from: 'child1', to: 'grandchild2' },
    { from: 'child2', to: 'grandchild3' },
    { from: 'grandchild1', to: 'great-grandchild1' },
    { from: 'grandchild1', to: 'great-grandchild2' },
    { from: 'grandchild2', to: 'great-grandchild3' },
    { from: 'grandchild3', to: 'great-grandchild4' },
    { from: 'grandchild3', to: 'great-grandchild5' }
  ]
};

// ノードとエッジからネスト構造を生成
function createNestedStructure(nodes, edges) {
  const nodeMap = new Map(nodes.map(node => [node.id, { ...node, children: [] }]));

  edges.forEach(edge => {
    const parentNode = nodeMap.get(edge.from);
    const childNode = nodeMap.get(edge.to);
    
    if (parentNode && childNode) {
      parentNode.children.push(childNode);
    }
  });

  return nodeMap.get('root');
}

// TreeNodeコンポーネント - 上辺と左辺だけのボーダーを持つ
const TreeNode = ({
  node,
  level = 0,
}: {
  node: NodeData;
  level?: number;
}) => {
  const hasChildren = node.children && node.children.length > 0;
  
  // ノードのスタイル - 上辺と左辺だけのボーダー
  const nodeStyle = {
    position: 'relative',
    paddingLeft: '24px',
    marginTop: '8px',
    borderLeft: '1px solid #ccc',
    borderTop: '1px solid #ccc',
    paddingTop: '8px',
    borderRight: 'none',
    borderBottom: 'none'
  };
  
  // ノード内のコンテンツスタイル
  const contentStyle = {
    paddingLeft: '4px'
  };
  
  // 子ノードのコンテナスタイル
  const childrenContainerStyle = {
    paddingLeft: '12px'
  };

  return (
    <div style={nodeStyle}>
      <div style={contentStyle}>{node.name}</div>
      
      {hasChildren && (
        <div style={childrenContainerStyle}>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// GraphViewコンポーネント - グラフ全体を管理する
const GraphView = () => {
  // ネスト構造を生成
  const nestedStructure = createNestedStructure(graphData.nodes, graphData.edges);
  
  const containerStyle = {
    padding: '16px'
  };
  
  return (
    <div style={containerStyle}>
      {nestedStructure && <TreeNode node={nestedStructure} />}
    </div>
  );
};

// Appコンポーネント
export function App() {
  const appStyle = {
    maxWidth: '800px',
    margin: '0 auto',
    backgroundColor: 'white',
    boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
    borderRadius: '4px',
    padding: '24px'
  };
  
  return (
    <div style={appStyle}>
      <GraphView />
    </div>
  );
}

// クライアントサイドでのレンダリング
if (typeof document !== 'undefined') {
  const rootElement = document.getElementById("root");
  if (rootElement) {
    const root = createRoot(rootElement);
    root.render(<App />);
  }
}
