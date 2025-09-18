'use client';

import { useState, useEffect, useRef } from 'react';

export const DuckDBCell = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [query, setQuery] = useState('SELECT 1 + 1 as result');
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [diagnosticResult, setDiagnosticResult] = useState<string | null>(null);
  const [isRunningDiagnostic, setIsRunningDiagnostic] = useState(false);
  const dbRef = useRef<any>(null);
  const connRef = useRef<any>(null);

  useEffect(() => {
    const initDuckDB = async () => {
      try {
        setError(null);
        
        // Load DuckDB from R2 via Worker endpoint
        const duckdb = await import('/r2/duckdb/duckdb-browser.mjs');
        
        const bundle = {
          mainModule: '/r2/duckdb/duckdb-mvp.wasm',
          mainWorker: '/r2/duckdb/duckdb-browser-mvp.worker.js'
        };
        
        // Initialize DuckDB with MVP bundle
        const db = await duckdb.instantiate(bundle);
        const conn = await db.connect();
        
        dbRef.current = db;
        connRef.current = conn;
        setIsLoaded(true);
        
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : String(err);
        setError(`Failed to initialize DuckDB: ${errorMessage}`);
        console.error('DuckDB initialization error:', err);
      }
    };
    
    initDuckDB();
    
    // Cleanup on unmount
    return () => {
      if (connRef.current) {
        try {
          connRef.current.close();
        } catch (e) {
          console.warn('Error closing DuckDB connection:', e);
        }
      }
      if (dbRef.current) {
        try {
          dbRef.current.terminate();
        } catch (e) {
          console.warn('Error terminating DuckDB:', e);
        }
      }
    };
  }, []);

  const runDiagnostic = async () => {
    setIsRunningDiagnostic(true);
    setDiagnosticResult(null);
    setError(null);
    
    const diagnostics = [];
    const startTime = performance.now();
    
    try {
      // Test 1: Check all 4 WASM assets from R2
      diagnostics.push('=== Asset Loading Test (R2) ===');
      const assets = [
        { url: '/r2/duckdb/duckdb-browser.mjs', name: 'Main Module' },
        { url: '/r2/duckdb/duckdb-mvp.wasm', name: 'WASM Binary' },
        { url: '/r2/duckdb/duckdb-browser-mvp.worker.js', name: 'Worker Script' },
        { url: '/r2/duckdb/duckdb-mvp.wasm.map', name: 'WASM Source Map' }
      ];
      
      for (const asset of assets) {
        try {
          const response = await fetch(asset.url, { method: 'HEAD' });
          const size = response.headers.get('content-length');
          const sizeKB = size ? (parseInt(size) / 1024).toFixed(1) : 'unknown';
          
          if (response.ok) {
            diagnostics.push(`✅ ${asset.name}: ${sizeKB} KB`);
          } else {
            diagnostics.push(`❌ ${asset.name}: HTTP ${response.status}`);
          }
        } catch (err) {
          diagnostics.push(`❌ ${asset.name}: Failed to fetch`);
        }
      }
      
      // Test 2: DuckDB initialization
      diagnostics.push('\n=== DuckDB Initialization Test ===');
      if (dbRef.current && connRef.current) {
        diagnostics.push('✅ DuckDB already initialized');
        
        // Test 3: Query execution
        diagnostics.push('\n=== Query Execution Test ===');
        try {
          const testQuery = 'SELECT version() as version, current_timestamp as ts';
          const stmt = await connRef.current.prepare(testQuery);
          const queryResult = await stmt.query();
          const rows = queryResult.toArray().map((row: any) => row.toJSON());
          
          if (rows.length > 0) {
            diagnostics.push(`✅ DuckDB Version: ${rows[0].version}`);
            diagnostics.push(`✅ Timestamp: ${rows[0].ts}`);
          }
          await stmt.close();
        } catch (err) {
          diagnostics.push(`❌ Query test failed: ${err}`);
        }
      } else {
        diagnostics.push('❌ DuckDB not initialized');
      }
      
      // Test 4: Network tab verification instructions
      diagnostics.push('\n=== Browser Network Tab Verification ===');
      diagnostics.push('Open DevTools Network tab and verify:');
      diagnostics.push('1. duckdb-browser.mjs loaded from /duckdb/');
      diagnostics.push('2. duckdb-mvp.wasm loaded from /duckdb/');
      diagnostics.push('3. duckdb-browser-mvp.worker.js loaded from /duckdb/');
      diagnostics.push('4. duckdb-mvp.wasm.map loaded from /duckdb/');
      diagnostics.push('All should show status 200 and NOT from CDN');
      
      const elapsed = (performance.now() - startTime).toFixed(2);
      diagnostics.push(`\n⏱️ Total diagnostic time: ${elapsed}ms`);
      
      setDiagnosticResult(diagnostics.join('\n'));
    } catch (err) {
      setError(`Diagnostic failed: ${err}`);
    } finally {
      setIsRunningDiagnostic(false);
    }
  };

  const executeQuery = async () => {
    if (!connRef.current || !query.trim()) return;
    
    setIsExecuting(true);
    setError(null);
    setResult('');
    
    try {
      const stmt = await connRef.current.prepare(query);
      const queryResult = await stmt.query();
      
      // Convert result to readable format
      const rows = queryResult.toArray().map((row: any) => row.toJSON());
      const formattedResult = JSON.stringify(rows, null, 2);
      
      setResult(formattedResult);
      
      await stmt.close();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(`Query execution failed: ${errorMessage}`);
      console.error('Query execution error:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      executeQuery();
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">DuckDB Query Interface</h2>
        
        {/* Status indicator */}
        <div className="mb-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium">
            {!isLoaded && !error && (
              <span className="bg-yellow-100 text-yellow-800">
                🔄 Initializing DuckDB...
              </span>
            )}
            {isLoaded && (
              <span className="bg-green-100 text-green-800">
                ✅ DuckDB Ready
              </span>
            )}
            {error && (
              <span className="bg-red-100 text-red-800">
                ❌ Error
              </span>
            )}
          </span>
        </div>

        {/* Query input */}
        <div className="mb-4">
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            SQL Query (Ctrl/Cmd + Enter to execute)
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isLoaded}
            className="w-full h-32 p-3 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            placeholder="Enter your SQL query here..."
          />
        </div>

        {/* Execute and Diagnostic buttons */}
        <div className="mb-4 flex gap-2">
          <button
            onClick={executeQuery}
            disabled={!isLoaded || isExecuting || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isExecuting ? (
              <>
                <span className="animate-spin">⏳</span>
                Executing...
              </>
            ) : (
              <>
                ▶️ Execute Query
              </>
            )}
          </button>
          
          <button
            onClick={runDiagnostic}
            disabled={isRunningDiagnostic}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isRunningDiagnostic ? (
              <>
                <span className="animate-spin">⏳</span>
                Diagnosing...
              </>
            ) : (
              <>
                🔍 Self-Diagnosis
              </>
            )}
          </button>
        </div>

        {/* Error display */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <h3 className="text-red-800 font-medium mb-1">Error</h3>
            <pre className="text-red-700 text-sm whitespace-pre-wrap">{error}</pre>
          </div>
        )}

        {/* Result display */}
        {result && (
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-800 mb-2">Results</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
              <pre className="text-sm overflow-auto max-h-96 whitespace-pre-wrap">{result}</pre>
            </div>
          </div>
        )}

        {/* Diagnostic result display */}
        {diagnosticResult && (
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-800 mb-2">Diagnostic Results</h3>
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <pre className="text-sm overflow-auto max-h-96 whitespace-pre-wrap font-mono">{diagnosticResult}</pre>
            </div>
          </div>
        )}

        {/* Usage tips */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
          <h3 className="text-blue-800 font-medium mb-2">💡 Usage Tips</h3>
          <ul className="text-blue-700 text-sm space-y-1">
            <li>• Use Ctrl/Cmd + Enter to execute queries quickly</li>
            <li>• Try: <code>SELECT * FROM range(10)</code> to generate sample data</li>
            <li>• Create tables with: <code>CREATE TABLE test AS SELECT 1 as id, 'hello' as name</code></li>
            <li>• DuckDB supports many SQL features including window functions, JSON, and arrays</li>
          </ul>
        </div>
      </div>
    </div>
  );
};