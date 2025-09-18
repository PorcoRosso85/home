'use client';

import { useState, useEffect, useRef } from 'react';

interface SQLiteR2LoaderProps {
  dbUrl: string;  // R2 URL for SQLite database file
  wasmUrl?: string; // WASM URL (optional, defaults to public)
}

export const SQLiteR2Loader = ({ 
  dbUrl, 
  wasmUrl = '/wasm/sqlite3.wasm' 
}: SQLiteR2LoaderProps) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [query, setQuery] = useState("SELECT name FROM sqlite_master WHERE type='table'");
  const [result, setResult] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dbSize, setDbSize] = useState<number>(0);
  const dbRef = useRef<any>(null);
  const sqliteRef = useRef<any>(null);

  useEffect(() => {
    const loadSQLiteFromR2 = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load SQLite WASM library
        const script = document.createElement('script');
        script.src = '/wasm/sqlite3.js';
        await new Promise((resolve, reject) => {
          script.onload = resolve;
          script.onerror = reject;
          document.body.appendChild(script);
        });

        // Wait for SQLite3 to be available
        while (!(window as any).sqlite3) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }

        const sqlite3 = (window as any).sqlite3;
        sqliteRef.current = sqlite3;

        // Initialize official SQLite WASM
        const sqlite3Module = await sqlite3.init({
          print: console.log,
          printErr: console.error
        });

        // Fetch database from R2
        console.log(`Fetching database from R2: ${dbUrl}`);
        const response = await fetch(dbUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch database from R2: ${response.status}`);
        }

        // Load database into memory
        const buffer = await response.arrayBuffer();
        const p = sqlite3Module.wasm.allocFromTypedArray(buffer);
        setDbSize(buffer.byteLength);

        // Open database from buffer
        const db = new sqlite3Module.oo1.DB();
        const rc = sqlite3Module.capi.sqlite3_deserialize(
          db.pointer, 'main', p, buffer.byteLength, buffer.byteLength,
          sqlite3Module.capi.SQLITE_DESERIALIZE_FREEONCLOSE
        );
        
        if (rc !== sqlite3Module.capi.SQLITE_OK) {
          throw new Error(`Failed to deserialize database: ${rc}`);
        }
        
        dbRef.current = db;

        // Test the database
        const tables = db.exec({
          sql: "SELECT name FROM sqlite_master WHERE type='table'",
          returnValue: "resultRows"
        });
        console.log('Database loaded. Tables:', tables);

        setIsLoaded(true);
        setError(null);
      } catch (err: any) {
        console.error('SQLite R2 load error:', err);
        setError(`Failed to load SQLite from R2: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadSQLiteFromR2();

    return () => {
      if (dbRef.current) {
        try {
          dbRef.current.close();
        } catch (e) {
          console.error('Error closing database:', e);
        }
      }
    };
  }, [dbUrl, wasmUrl]);

  const executeQuery = () => {
    if (!dbRef.current) {
      setError('Database not loaded');
      return;
    }

    setLoading(true);
    setError(null);
    setResult([]);

    try {
      // Execute query using official SQLite WASM API
      const results = dbRef.current.exec({
        sql: query,
        returnValue: "resultRows",
        rowMode: "object"
      });
      
      // Convert to expected format
      const formattedResults = results.length > 0 ? [{
        columns: Object.keys(results[0]),
        values: results.map(row => Object.values(row))
      }] : [];
      
      setResult(formattedResults);
    } catch (err: any) {
      setError(`Query error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatResults = (results: any[]) => {
    if (!results || results.length === 0) {
      return <div style={{ color: '#6b7280' }}>No results</div>;
    }

    return results.map((result, idx) => (
      <div key={idx} style={{ marginBottom: '16px' }}>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          fontSize: '14px' 
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f3f4f6' }}>
              {result.columns.map((col: string, i: number) => (
                <th key={i} style={{ 
                  padding: '8px', 
                  textAlign: 'left',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.values.map((row: any[], rowIdx: number) => (
              <tr key={rowIdx} style={{ 
                backgroundColor: rowIdx % 2 === 0 ? 'white' : '#f9fafb' 
              }}>
                {row.map((val: any, colIdx: number) => (
                  <td key={colIdx} style={{ 
                    padding: '8px',
                    borderBottom: '1px solid #e5e7eb'
                  }}>
                    {val === null ? <em>NULL</em> : String(val)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ));
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
        SQLite from R2
      </h3>

      {loading && !isLoaded && (
        <div style={{ marginBottom: '16px', color: '#3b82f6' }}>
          Loading database from R2...
        </div>
      )}

      {isLoaded && (
        <>
          <div style={{ 
            marginBottom: '16px', 
            padding: '8px',
            backgroundColor: '#f0f9ff',
            borderRadius: '4px',
            fontSize: '14px'
          }}>
            Database loaded from R2 ({(dbSize / 1024).toFixed(2)} KB)
          </div>

          <div style={{ marginBottom: '16px' }}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter SQL query..."
              style={{
                width: '100%',
                minHeight: '100px',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '14px'
              }}
            />
          </div>

          <button
            onClick={executeQuery}
            disabled={loading}
            style={{
              padding: '8px 16px',
              backgroundColor: loading ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              marginBottom: '16px'
            }}
          >
            {loading ? 'Executing...' : 'Execute Query'}
          </button>

          {error && (
            <div style={{
              padding: '12px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '4px',
              color: '#dc2626',
              marginBottom: '16px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          {result.length > 0 && (
            <div style={{
              maxHeight: '400px',
              overflowY: 'auto',
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              padding: '8px'
            }}>
              {formatResults(result)}
            </div>
          )}
        </>
      )}
    </section>
  );
};