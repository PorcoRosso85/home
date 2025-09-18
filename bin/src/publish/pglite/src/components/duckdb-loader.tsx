'use client';

import { useState, lazy, Suspense } from 'react';

// Lazy load the DuckDB component
const DuckDBR2Demo = lazy(() => import('./duckdb-r2-demo').then(module => ({
  default: module.DuckDBR2Demo
})));

interface DuckDBLoaderProps {
  enableR2?: boolean;
  r2Url?: string;
}

export const DuckDBLoader = ({ enableR2 = false, r2Url }: DuckDBLoaderProps) => {
  const [shouldLoad, setShouldLoad] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleLoadDuckDB = () => {
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
          DuckDB WASM Query Demo
        </h3>
        <p style={{ marginBottom: '16px', fontSize: '14px', color: '#6b7280' }}>
          DuckDB WASMを使用してブラウザ上でSQLクエリを実行できます。
          利用するには約45MBのダウンロードが必要です。
        </p>
        <button
          onClick={handleLoadDuckDB}
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
          {isLoading ? 'Loading DuckDB...' : 'Load DuckDB (45MB)'}
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
          Loading DuckDB WASM...
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
        <p style={{ marginTop: '16px', fontSize: '14px', color: '#6b7280' }}>
          Downloading DuckDB WASM modules (~45MB)...
        </p>
      </section>
    }>
      <DuckDBR2Demo enableR2={enableR2} r2Url={r2Url} />
    </Suspense>
  );
};