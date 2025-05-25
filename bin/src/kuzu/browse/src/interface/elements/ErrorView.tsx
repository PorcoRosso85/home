/**
 * エラー状態の表示コンポーネント
 */
import React from 'react';

interface ErrorViewProps {
  error: Error | string | null;
}

export const ErrorView: React.FC<ErrorViewProps> = ({ error }) => {
  const errorMessage = error instanceof Error ? error.message : error || 'Unknown error';
  
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      fontFamily: 'Arial, sans-serif',
      color: 'red'
    }}>
      <div>Error: {errorMessage}</div>
    </div>
  );
};
