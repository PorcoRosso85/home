'use client';

import { useState, lazy, Suspense, ComponentType } from 'react';

interface R2WASMLoaderProps {
  name: string;
  wasmPath: string;
  displayName: string;
  estimatedSize: string;
  componentPath: string;
  r2BaseUrl?: string;
}

export const R2WASMLoader = ({ 
  name,
  wasmPath,
  displayName,
  estimatedSize,
  componentPath,
  r2BaseUrl = process.env.NEXT_PUBLIC_R2_WASM_URL || ''
}: R2WASMLoaderProps) => {
  const [shouldLoad, setShouldLoad] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dynamic import of the actual WASM component
  const WASMComponent = lazy(async () => {
    try {
      const module = await import(componentPath);
      return { default: module.default || module[Object.keys(module)[0]] };
    } catch (err) {
      console.error(`Failed to load component: ${componentPath}`, err);
      setError(`Failed to load ${displayName} component`);
      return { default: () => <div>Failed to load component</div> };
    }
  });

  const handleLoad = () => {
    if (!r2BaseUrl) {
      setError('R2 WASM URL not configured. Please set R2_WASM_URL environment variable.');
      return;
    }
    setIsLoading(true);
    setShouldLoad(true);
  };

  const wasmUrl = r2BaseUrl ? `${r2BaseUrl}/${wasmPath}` : '';

  if (error) {
    return (
      <section style={{
        border: '1px dashed #ef4444',
        borderRadius: '2px',
        marginTop: '16px',
        marginLeft: '-16px',
        marginRight: '-16px',
        padding: '16px',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, sans-serif'
      }}>
        <h3 style={{ margin: 0, marginBottom: '16px', fontSize: '1.125rem', color: '#dc2626' }}>
          Error Loading {displayName}
        </h3>
        <p style={{ fontSize: '14px', color: '#7f1d1d' }}>
          {error}
        </p>
      </section>
    );
  }

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
          {displayName} WASM Demo
        </h3>
        <p style={{ marginBottom: '8px', fontSize: '14px', color: '#6b7280' }}>
          {displayName} WASMをCloudflare R2から読み込みます。
        </p>
        <p style={{ marginBottom: '16px', fontSize: '12px', color: '#9ca3af' }}>
          ファイルサイズ: 約{estimatedSize} | ソース: {r2BaseUrl ? 'R2' : 'Not configured'}
        </p>
        <button
          onClick={handleLoad}
          disabled={isLoading || !r2BaseUrl}
          style={{
            padding: '12px 24px',
            backgroundColor: r2BaseUrl ? '#3b82f6' : '#9ca3af',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: r2BaseUrl ? 'pointer' : 'not-allowed',
            fontSize: '14px',
            fontWeight: '500',
            transition: 'background-color 0.2s',
          }}
          onMouseEnter={(e) => {
            if (r2BaseUrl) e.currentTarget.style.backgroundColor = '#2563eb';
          }}
          onMouseLeave={(e) => {
            if (r2BaseUrl) e.currentTarget.style.backgroundColor = '#3b82f6';
          }}
        >
          {isLoading ? `Loading ${displayName}...` : `Load ${displayName} (${estimatedSize})`}
        </button>
        {!r2BaseUrl && (
          <div style={{
            marginTop: '12px',
            padding: '8px',
            backgroundColor: '#fef3c7',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#92400e'
          }}>
            ⚠️ R2 WASM URL not configured. Set R2_WASM_URL in environment variables.
          </div>
        )}
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
          Loading {displayName} from R2...
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
          Downloading from: {wasmUrl}
        </p>
      </section>
    }>
      <WASMComponent wasmUrl={wasmUrl} />
    </Suspense>
  );
};