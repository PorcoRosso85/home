'use client';

import { useState, useEffect, useRef } from 'react';

interface SQLiteDemoProps {
  wasmUrl?: string;
}

export const SQLiteDemo = ({ wasmUrl = '/wasm/sqlite3.wasm' }: SQLiteDemoProps) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [query, setQuery] = useState("SELECT sqlite_version()");
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dbRef = useRef<any>(null);

  useEffect(() => {
    const loadSQLite = async () => {
      try {
        // Method 1: Load from local public directory
        // The WASM file should be placed in public/wasm/sqlite3.wasm
        const response = await fetch(wasmUrl);
        if (!response.ok) {
          throw new Error(`Failed to load WASM from ${wasmUrl}`);
        }

        // For actual SQLite WASM, you would initialize it here
        // This is a placeholder for the actual implementation
        // Example with sql.js:
        // const sqlJs = await initSqlJs({
        //   locateFile: file => `/wasm/${file}`
        // });
        // const db = new sqlJs.Database();
        // dbRef.current = db;

        setIsLoaded(true);
        setError(null);
      } catch (err: any) {
        console.error('SQLite init error:', err);
        setError('Failed to initialize SQLite: ' + err.message);
      }
    };

    loadSQLite();

    return () => {
      if (dbRef.current) {
        // Clean up database connection
        // dbRef.current.close();
      }
    };
  }, [wasmUrl]);

  const executeQuery = async () => {
    if (!dbRef.current && isLoaded) {
      // Demo mode - show example output
      setLoading(true);
      setTimeout(() => {
        setResult('SQLite version: 3.45.0 (demo)\nNote: Actual SQLite WASM implementation required');
        setLoading(false);
      }, 500);
      return;
    }

    setLoading(true);
    setError(null);
    setResult('');

    try {
      // Execute actual SQLite query when WASM is properly loaded
      // const results = dbRef.current.exec(query);
      // Format and display results...
      
      setResult('Query execution would happen here');
    } catch (err: any) {
      setError(err.message || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

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

        <div style={{ marginBottom: '16px' }}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter SQL query..."
            style={{
              width: '100%',
              minHeight: '60px',
              padding: '8px',
              fontFamily: 'monospace',
              fontSize: '13px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <button
            onClick={executeQuery}
            disabled={!isLoaded || loading}
            style={{
              padding: '8px 16px',
              backgroundColor: isLoaded && !loading ? '#3b82f6' : '#9ca3af',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoaded && !loading ? 'pointer' : 'not-allowed',
              fontSize: '14px'
            }}
          >
            {loading ? 'Running...' : !isLoaded ? 'Loading SQLite...' : 'Execute'}
          </button>
        </div>

        {result && (
          <pre style={{
            padding: '12px',
            backgroundColor: '#f9fafb',
            border: '1px solid #e5e7eb',
            borderRadius: '4px',
            fontSize: '12px',
            overflow: 'auto'
          }}>
            {result}
          </pre>
        )}

        {error && (
          <div style={{
            padding: '12px',
            backgroundColor: '#fee2e2',
            border: '1px solid #ef4444',
            borderRadius: '4px',
            color: '#b91c1c',
            fontSize: '13px'
          }}>
            {error}
          </div>
        )}

        <div style={{
          marginTop: '16px',
          padding: '8px',
          backgroundColor: '#fef3c7',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#92400e'
        }}>
          <strong>WASM Loading Methods:</strong>
          <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
            <li>Local: Place WASM files in public/wasm/</li>
            <li>R2: Upload to R2 and use custom URL</li>
            <li>NPM: Install package and copy during build</li>
          </ul>
          <p style={{ marginTop: '8px' }}>
            Current URL: {wasmUrl}
          </p>
        </div>
    </section>
  );
};