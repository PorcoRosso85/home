'use client';

import { useState } from 'react';
import { 
  initKuzu, 
  createSampleGraph, 
  executeQuery, 
  sampleQueries,
  testKuzu 
} from '../lib/kuzu-example';

export default function KuzuDemo() {
  const [status, setStatus] = useState<string>('Not initialized');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState('findPeopleWithCities');
  const [customQuery, setCustomQuery] = useState('');

  const handleInit = async () => {
    setLoading(true);
    try {
      await initKuzu();
      setStatus('Kuzu initialized successfully');
    } catch (error) {
      setStatus(`Failed to initialize: ${error}`);
    }
    setLoading(false);
  };

  const handleCreateSample = async () => {
    setLoading(true);
    try {
      await createSampleGraph();
      setStatus('Sample graph created');
    } catch (error) {
      setStatus(`Failed to create sample: ${error}`);
    }
    setLoading(false);
  };

  const handleRunQuery = async (query: string) => {
    setLoading(true);
    try {
      const result = await executeQuery(query);
      setQueryResult(result);
      setStatus('Query executed');
    } catch (error) {
      setStatus(`Query failed: ${error}`);
    }
    setLoading(false);
  };

  const handleTest = async () => {
    setLoading(true);
    try {
      const result = await testKuzu();
      setQueryResult(result);
      setStatus(result.message);
    } catch (error) {
      setStatus(`Test failed: ${error}`);
    }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Kuzu WASM Demo</h1>
      
      <div className="mb-6 p-4 bg-gray-100 rounded">
        <p className="text-sm">Status: <span className="font-mono">{status}</span></p>
      </div>

      <div className="space-y-4">
        <div className="flex gap-2">
          <button
            onClick={handleInit}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            Initialize Kuzu
          </button>
          
          <button
            onClick={handleCreateSample}
            disabled={loading}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            Create Sample Graph
          </button>
          
          <button
            onClick={handleTest}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
          >
            Run Full Test
          </button>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-xl font-semibold mb-2">Sample Queries</h2>
          
          <select
            value={selectedQuery}
            onChange={(e) => setSelectedQuery(e.target.value)}
            className="w-full p-2 border rounded mb-2"
          >
            {Object.entries(sampleQueries).map(([key, query]) => (
              <option key={key} value={key}>
                {key.replace(/([A-Z])/g, ' $1').trim()}
              </option>
            ))}
          </select>
          
          <button
            onClick={() => handleRunQuery(sampleQueries[selectedQuery as keyof typeof sampleQueries])}
            disabled={loading}
            className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 disabled:opacity-50"
          >
            Run Selected Query
          </button>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-xl font-semibold mb-2">Custom Query</h2>
          
          <textarea
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="Enter your Cypher query here..."
            className="w-full p-2 border rounded h-24 font-mono text-sm"
          />
          
          <button
            onClick={() => handleRunQuery(customQuery)}
            disabled={loading || !customQuery}
            className="mt-2 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
          >
            Run Custom Query
          </button>
        </div>

        {queryResult && (
          <div className="border-t pt-4">
            <h2 className="text-xl font-semibold mb-2">Query Result</h2>
            <pre className="p-4 bg-gray-900 text-green-400 rounded overflow-auto">
              {JSON.stringify(queryResult, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <h3 className="font-semibold text-yellow-800 mb-2">About this Demo</h3>
        <p className="text-sm text-yellow-700">
          This demo shows Kuzu-wasm running in a Cloudflare Worker environment.
          The WASM files from @kuzu/kuzu-wasm are automatically handled by @cloudflare/vite-plugin
          during the build process, enabling in-browser graph database operations.
        </p>
      </div>
    </div>
  );
}