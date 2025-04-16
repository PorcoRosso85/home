import React, { useState, useEffect } from 'https://esm.sh/react@18.2.0';
import TreeNode from './src/components/TreeNode';
import NodeService from './src/infrastructure/NodeService';
import { FrontendNodeType, HighlightDataType } from './src/types';

// ツリー表示コンポーネント（相対番号表示）
const App = () => {
  // サービスのインスタンス化
  const nodeService = new NodeService();
  
  // 状態
  const [selectedFunction, setSelectedFunction] = useState<string | null>(null);
  const [highlightData, setHighlightData] = useState<HighlightDataType>({
    _minPosition: 0,
    _maxPosition: 0,
    _boxCount: 0
  });
  const [callerDepth, setCallerDepth] = useState<number | Infinity>(Infinity); // 呼び出し元の深さ（Infinity=無制限）
  const [calleeDepth, setCalleeDepth] = useState<number | Infinity>(Infinity); // 呼び出し先の深さ（Infinity=無制限）
  const [nestedStructure, setNestedStructure] = useState<FrontendNodeType>({ id: 'loading', name: 'Loading...', path: '' });
  const [maxDepth, setMaxDepth] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  // NOTE: LocalStorage使用をいったんコメントアウト
  // const [storageInfo, setStorageInfo] = useState<{ used: number; total: number; percentage: number }>({ used: 0, total: 0, percentage: 0 });
  
  // 初期データの読み込み
  useEffect(() => {
    loadInitialData();
    // NOTE: LocalStorage使用をいったんコメントアウト
    // updateStorageInfo();
  }, []);
  
  // NOTE: LocalStorage使用をいったんコメントアウト
  /*
  // LocalStorage使用状況の更新
  const updateStorageInfo = () => {
    const info = nodeService.getStorageInfo();
    setStorageInfo(info);
  };
  */
  
  // データのリセット処理
  const handleResetData = async () => {
    if (window.confirm('すべてのデータをリセットして公開ファイルから再読み込みしますか？')) {
      setIsLoading(true);
      await nodeService.resetAllData();
      await loadInitialData();
      // NOTE: LocalStorage使用をいったんコメントアウト
      // updateStorageInfo();
    }
  };
  
  // 初期データの読み込み
  const loadInitialData = async () => {
    try {
      console.log("初期データのロード開始...");
      // ネスト構造の取得
      const structure = await nodeService.getNestedStructure();
      console.log("ネスト構造取得完了:", structure.id, structure.name);
      
      if (structure.id === 'empty') {
        console.warn("警告: 空のデータ構造が返されました。パス設計を確認してください。");
        // デバッグ用にノードデータを直接表示
        const nodesData = await nodeService.getNodes();
        console.log("ノードデータ直接表示:", Object.keys(nodesData).length, Object.keys(nodesData).slice(0, 3));
        
        // メタデータの実装パスの形式確認
        const nodesWithPath = Object.values(nodesData).filter(node => node.metadata?.implementation?.location?.path).length;
        console.log(`メタデータにパスを持つノード数: ${nodesWithPath}/${Object.keys(nodesData).length}`);
        
        // サンプルノードの詳細を表示
        if (Object.keys(nodesData).length > 0) {
          const sampleNode = Object.values(nodesData)[0];
          console.log("サンプルノード詳細:", {
            id: sampleNode.id,
            name: sampleNode.name,
            type: sampleNode.type,
            path: sampleNode.metadata?.implementation?.location?.path || "パスなし"
          });
        }
      }
      
      setNestedStructure(structure);
      
      // 最大深度の計算
      const depth = nodeService.calculateMaxDepth(structure);
      console.log(`最大深度計算結果: ${depth}`);
      setMaxDepth(depth);
      
      // ルート関数を取得して最初の関数を選択
      const rootFunctions = await nodeService.getRootFunctions();
      console.log(`ルート関数取得結果: ${rootFunctions.length}個`, rootFunctions.slice(0, 3));
      
      if (rootFunctions.length > 0) {
        const rootFunction = rootFunctions[0];
        setSelectedFunction(rootFunction);
        await handleNodeClick({ id: rootFunction, name: rootFunction.split(':::')[1] || rootFunction, path: rootFunction });
      } else {
        console.warn("ルート関数がありません。エッジデータを確認してください。");
        // エッジデータを直接表示
        const edgesData = await nodeService.getEdges();
        console.log(`エッジデータ: ${edgesData.length}個`);
        if (edgesData.length > 0) {
          console.log("サンプルエッジ:", edgesData[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 関数を選択したときの処理
  const handleNodeClick = async (node: FrontendNodeType) => {
    // 関数ノードのみ処理
    if (node.path.includes(':::')) {
      setSelectedFunction(node.path);
      console.log(`関数選択: ${node.path}`);
      
      try {
        // 依存関係のデータを取得して確認
        const dependencies = await nodeService.getFunctionDependencies();
        console.log(`依存関係データ: ${dependencies.length}件`, dependencies.slice(0, 3));
        
        // ハイライトデータを計算
        const data = await nodeService.getHighlightData(
          node.path,
          typeof callerDepth === 'number' ? callerDepth : Number.MAX_SAFE_INTEGER,
          typeof calleeDepth === 'number' ? calleeDepth : Number.MAX_SAFE_INTEGER
        );
        
        console.log("ハイライトデータ:", data);
        console.log(`ハイライト範囲: ${data._minPosition} 〜 ${data._maxPosition}, ボックス数: ${data._boxCount}`);
        
        // 選択した関数に対応するハイライトがあるか確認
        if (data[node.path] !== undefined) {
          console.log(`選択関数のハイライト位置: ${data[node.path]}`);
        } else {
          console.warn(`警告: 選択関数 ${node.path} に対応するハイライトがありません`);
        }
        
        setHighlightData(data);
      } catch (error) {
        console.error('Failed to get highlight data:', error);
      }
    } else {
      console.log(`非関数ノード選択: ${node.path}`);
    }
  };
  
  // 呼び出し元の深さを変更する処理
  const handleCallerDepthChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setCallerDepth(value === "Infinity" ? Infinity : parseInt(value, 10));
    
    // 選択中の関数があれば再計算
    if (selectedFunction) {
      await handleNodeClick({ id: selectedFunction, name: selectedFunction.split(':::')[1] || selectedFunction, path: selectedFunction });
    }
  };
  
  // 呼び出し先の深さを変更する処理
  const handleCalleeDepthChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setCalleeDepth(value === "Infinity" ? Infinity : parseInt(value, 10));
    
    // 選択中の関数があれば再計算
    if (selectedFunction) {
      await handleNodeClick({ id: selectedFunction, name: selectedFunction.split(':::')[1] || selectedFunction, path: selectedFunction });
    }
  };
  
  // 現在のボックス数と範囲を取得
  const boxCount = highlightData._boxCount || 0;
  const minPosition = highlightData._minPosition || 0;
  const maxPosition = highlightData._maxPosition || 0;
  
  // ロード中の表示
  if (isLoading) {
    return (
      <div style={{ 
        maxWidth: '1000px', 
        margin: '0 auto', 
        padding: '20px',
        fontFamily: 'Arial, sans-serif',
        textAlign: 'center'
      }}>
        <h2>Loading...</h2>
        <p>データを読み込んでいます...</p>
      </div>
    );
  }
  
  // メイン表示
  return (
    <div style={{ 
      maxWidth: '1000px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f9f9f9',
      borderRadius: '8px'
    }}>
      <h2 style={{ marginBottom: '10px' }}>関数依存関係に基づくツリー表示</h2>
      <p style={{ marginBottom: '20px', color: '#666' }}>
        選択した関数を中心(0)として、呼び出し元は負の数({minPosition}～-1)、呼び出し先は正の数(1～{maxPosition})で表示されます。使用ボックス数: {boxCount}個
      </p>
      {/* NOTE: LocalStorage使用をいったんコメントアウト
      <p style={{ marginBottom: '20px', color: '#0066cc', fontSize: '0.9em' }}>
        LocalStorage使用量: {Math.round(storageInfo.used / 1024)}KB / {Math.round(storageInfo.total / 1024 / 1024)}MB ({storageInfo.percentage.toFixed(1)}%)
      </p>
      */}
      
      <div style={{ overflow: 'auto' }}>
        <TreeNode
          node={nestedStructure}
          maxDepth={maxDepth}
          highlightData={highlightData}
          onNodeClick={handleNodeClick}
        />
      </div>
    </div>
  );
};

export default App;