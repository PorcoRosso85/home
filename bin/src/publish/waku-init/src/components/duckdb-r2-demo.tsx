'use client';

import { useState, useEffect, useRef } from 'react';

interface DuckDBR2DemoProps {
  enableR2?: boolean;
  r2Url?: string;
}

export const DuckDBR2Demo = ({ enableR2 = false, r2Url }: DuckDBR2DemoProps) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [query, setQuery] = useState("SELECT 1 + 1 as result");
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dbRef = useRef<any>(null);
  const connRef = useRef<any>(null);

  useEffect(() => {
    // Load DuckDB from CDN - using ESM module
    const loadDuckDB = async () => {
      try {
        // Dynamic import of DuckDB WASM ESM module
        const duckdbModule = await import('https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@latest/+esm');
        // @ts-ignore
        window.duckdb = duckdbModule;
        initDuckDB();
      } catch (err) {
        console.error('Failed to load DuckDB module:', err);
        setError('Failed to load DuckDB module');
      }
    };

    loadDuckDB();

    return () => {
      if (connRef.current) {
        connRef.current.close();
      }
      if (dbRef.current) {
        dbRef.current.terminate();
      }
    };
  }, []);

  // Use CDN for DuckDB WASM
  const initDuckDB = async () => {
    try {
      // @ts-ignore - Global from CDN
      if (!window.duckdb) {
        setError('DuckDB not loaded yet');
        return;
      }

      // @ts-ignore  
      const duckdb = window.duckdb;
      
      // Use jsDelivr bundles
      const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();
      const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);
      
      // Create worker
      const worker_url = URL.createObjectURL(
        new Blob([`importScripts("${bundle.mainWorker}");`], { 
          type: 'text/javascript' 
        })
      );
      
      const worker = new Worker(worker_url);
      const logger = new duckdb.ConsoleLogger();
      const db = new duckdb.AsyncDuckDB(logger, worker);
      
      await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
      URL.revokeObjectURL(worker_url);
      
      const conn = await db.connect();
      
      dbRef.current = db;
      connRef.current = conn;
      setIsLoaded(true);
      setError(null);
    } catch (err: any) {
      console.error('DuckDB init error:', err);
      setError('Failed to initialize DuckDB: ' + err.message);
    }
  };

  const executeQuery = async () => {
    if (!connRef.current) {
      setError('Database not connected');
      return;
    }

    setLoading(true);
    setError(null);
    setResult('');

    try {
      const queryResult = await connRef.current.query(query);
      
      // Format result as simple text
      const columns = queryResult.schema.fields.map((f: any) => f.name);
      const rows = queryResult.toArray();
      
      let output = columns.join(' | ') + '\n';
      output += '-'.repeat(columns.join(' | ').length) + '\n';
      
      rows.forEach((row: any) => {
        const values = columns.map((col: string) => String(row[col]));
        output += values.join(' | ') + '\n';
      });
      
      setResult(output);
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
          DuckDB WASM Query Demo {enableR2 ? '(R2 Enabled)' : '(Local Mode)'}
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
            {loading ? 'Running...' : !isLoaded ? 'Loading DuckDB...' : 'Execute'}
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

        {enableR2 && r2Url && (
          <div style={{
            marginTop: '16px',
            padding: '8px',
            backgroundColor: '#f0f9ff',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#1e40af'
          }}>
            <strong>Example R2 queries:</strong>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
              <li>SELECT * FROM '{r2Url}/data.parquet' LIMIT 10</li>
              <li>SELECT COUNT(*) FROM read_parquet('{r2Url}/data.parquet')</li>
            </ul>
          </div>
        )}
    </section>
  );
};