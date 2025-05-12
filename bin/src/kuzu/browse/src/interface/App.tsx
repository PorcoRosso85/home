/**
 * KuzuDB Graph Browser のメインアプリケーションコンポーネント
 */
import React from 'react';
import { VersionTreeView } from './components/VersionTreeView';

/**
 * アプリケーションのメインコンポーネント
 */
const App: React.FC = () => {
  return (
    <div style={{ 
      padding: '20px',
      maxWidth: '1200px',
      margin: '0 auto',
      fontFamily: 'Arial, sans-serif'
    }}>
      <main>
        <VersionTreeView />
      </main>
    </div>
  );
};

export default App;
