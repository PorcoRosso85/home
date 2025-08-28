'use client';

import { useState, lazy, Suspense } from 'react';

// Lazy load the SQLite component
const SQLiteDemo = lazy(() => import('./sqlite-demo').then(module => ({
  default: module.SQLiteDemo
})));

interface SQLiteLoaderProps {
  wasmUrl?: string; // Custom WASM URL (e.g., from R2 or local public)
}

export const SQLiteLoader = ({ wasmUrl = '/wasm/sqlite3.wasm' }: SQLiteLoaderProps) => {
  const [shouldLoad, setShouldLoad] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleLoadSQLite = () => {
    setIsLoading(true);
    setShouldLoad(true);
  };

  if (!shouldLoad) {
    return (
      <section style={{
        border: '1px dashed #60a5fa',
        borderRadius: '2px',
        marginTop: '16px',
        marginLeft: '-16px',
        marginRight: '-16px',
        padding: '16px',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, sans-serif'
      }}>
        <h3 style={{ margin: 0, marginBottom: '16px', fontSize: '1.125rem' }}>
          SQLite WASM Demo
        </h3>
        <p style={{ marginBottom: '16px', fontSize: '14px', color: '#6b7280' }}>
          SQLite WASMを使用してブラウザ上でSQLクエリを実行できます。
          WASMファイルはローカルまたはR2から読み込まれます。
        </p>
        <button
          onClick={handleLoadSQLite}
          disabled={isLoading}
          style={{
            padding: '12px 24px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            transition: 'background-color 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
        >
          {isLoading ? 'Loading SQLite...' : 'Load SQLite WASM'}
        </button>
      </section>
    );
  }

  return (
    <Suspense fallback={
      <section style={{
        border: '1px dashed #60a5fa',
        borderRadius: '2px',
        marginTop: '16px',
        marginLeft: '-16px',
        marginRight: '-16px',
        padding: '16px',
        textAlign: 'center',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, sans-serif'
      }}>
        <h3 style={{ margin: 0, marginBottom: '16px', fontSize: '1.125rem' }}>
          Loading SQLite WASM...
        </h3>
        <div style={{
          display: 'inline-block',
          width: '50px',
          height: '50px',
          border: '3px solid #e5e7eb',
          borderTop: '3px solid #3b82f6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </section>
    }>
      <SQLiteDemo wasmUrl={wasmUrl} />
    </Suspense>
  );
};