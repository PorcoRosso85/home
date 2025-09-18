/**
 * KuzuDB Graph Browser のメインアプリケーションコンポーネント
 */
import React from 'react';
import { Layout } from './Layout';
import { Page } from './Page';

/**
 * アプリケーションのメインコンポーネント
 */
const App: React.FC = () => {
  return (
    <Layout>
      <Page />
    </Layout>
  );
};

export default App;