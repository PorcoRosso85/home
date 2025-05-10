import React from 'react';
import { LoadingView } from './components/LoadingView';
import { ErrorView } from './components/ErrorView';
import { TreeView } from './components/TreeView';
// import { NodeDetailsPanel } from './components/NodeDetailsPanel';
import { useDatabaseConnection } from '../infrastructure/database/useDatabaseConnection';
import { useTreeData } from '../application/hooks/useTreeData';

const App = () => {
  const { isConnected, error: dbError } = useDatabaseConnection();
  const { treeData, /* selectedNode, handleNodeClick, */ isLoading, error } = useTreeData();

  if (!isConnected || isLoading) {
    return <LoadingView />;
  }

  if (dbError || error) {
    return <ErrorView error={dbError || error} />;
  }

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <TreeView 
        treeData={treeData} 
        // onNodeClick={handleNodeClick} 
      />
      {/* <NodeDetailsPanel selectedNode={selectedNode} /> */}
    </div>
  );
};

export default App;
