'use client';

import { useState } from 'react';
import { submitAsLog, batchProcessLogs } from '../server/log-actions';

export const LogFormDemo = () => {
  const [status, setStatus] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    
    const result = await submitAsLog(formData);
    const logMessage = `[${new Date().toISOString()}] ${result.message} (ID: ${result.logId})`;
    setLogs(prev => [...prev, logMessage]);
    setStatus(result.success ? 'success' : 'error');
    
    if (result.success) {
      (e.target as HTMLFormElement).reset();
    }
  };

  const handleBatch = async () => {
    const result = await batchProcessLogs();
    setLogs(prev => [...prev, `[BATCH] Processed ${result.processed} logs → R2: ${result.outputKey}`]);
  };

  return (
    <div style={{ 
      border: '2px solid #3b82f6', 
      borderRadius: '8px', 
      padding: '20px',
      backgroundColor: '#f0f9ff'
    }}>
      <h2>🪵 Log-Based Form (Local Simulation)</h2>
      
      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <div style={{ marginBottom: '10px' }}>
          <input
            name="name"
            placeholder="Name"
            required
            style={{ width: '100%', padding: '8px', marginBottom: '8px' }}
          />
          <input
            name="email"
            type="email"
            placeholder="Email"
            required
            style={{ width: '100%', padding: '8px', marginBottom: '8px' }}
          />
          <input
            name="subject"
            placeholder="Subject"
            required
            style={{ width: '100%', padding: '8px', marginBottom: '8px' }}
          />
          <textarea
            name="message"
            placeholder="Message"
            required
            style={{ width: '100%', padding: '8px', minHeight: '80px' }}
          />
        </div>
        
        <button type="submit" style={{
          backgroundColor: '#3b82f6',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          marginRight: '10px'
        }}>
          Submit (→ Log)
        </button>
        
        <button type="button" onClick={handleBatch} style={{
          backgroundColor: '#10b981',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}>
          Run Batch Process
        </button>
      </form>

      {status && (
        <div style={{
          padding: '10px',
          backgroundColor: status === 'success' ? '#d1fae5' : '#fee2e2',
          borderRadius: '4px',
          marginBottom: '10px'
        }}>
          {status === 'success' ? '✅ Logged' : '❌ Failed'}
        </div>
      )}

      <div style={{
        backgroundColor: '#1e293b',
        color: '#10b981',
        padding: '10px',
        borderRadius: '4px',
        fontFamily: 'monospace',
        fontSize: '12px',
        maxHeight: '200px',
        overflow: 'auto'
      }}>
        <div style={{ color: '#94a3b8', marginBottom: '5px' }}>📊 Log Output:</div>
        {logs.length === 0 && <div style={{ color: '#64748b' }}>No logs yet...</div>}
        {logs.map((log, i) => (
          <div key={i} style={{ marginBottom: '2px' }}>{log}</div>
        ))}
      </div>

      <div style={{
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#fef3c7',
        borderRadius: '4px',
        fontSize: '13px'
      }}>
        <strong>💡 How it works (Workers Environment):</strong>
        <ol style={{ margin: '5px 0 0 20px', padding: 0 }}>
          <li>Form submit → console.log → Cloudflare Logs</li>
          <li>Optional: Buffer in KV Storage</li>
          <li>Batch process → Aggregate to R2 as JSONL</li>
          <li>DuckDB queries R2 JSONL files directly!</li>
        </ol>
      </div>
    </div>
  );
};