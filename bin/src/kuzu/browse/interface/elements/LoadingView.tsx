/**
 * ローディング状態の表示コンポーネント
 */
import React from 'react';

export const LoadingView: React.FC = () => {
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
};
