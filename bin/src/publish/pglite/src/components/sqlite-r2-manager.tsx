'use client';

import { useState, useEffect } from 'react';
import { SQLiteR2Loader } from './sqlite-r2-loader';

interface Database {
  name: string;
  size: number;
  uploaded: string;
  url: string;
}

export const SQLiteR2Manager = () => {
  const [databases, setDatabases] = useState<Database[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');

  // Fetch list of databases
  const fetchDatabases = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/sqlite/list');
      if (response.ok) {
        const data = await response.json();
        setDatabases(data.databases || []);
      }
    } catch (error) {
      console.error('Failed to fetch databases:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatabases();
  }, []);

  // Handle file upload
  const handleUpload = async () => {
    if (!uploadFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('database', uploadFile);
    formData.append('name', uploadName || uploadFile.name);

    try {
      const response = await fetch('/api/sqlite/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Upload successful:', result);
        await fetchDatabases();
        setUploadFile(null);
        setUploadName('');
      } else {
        console.error('Upload failed:', await response.text());
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle database deletion
  const handleDelete = async (name: string) => {
    if (!confirm(`Delete database ${name}?`)) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/sqlite/db/${name}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await fetchDatabases();
        if (selectedDb === name) {
          setSelectedDb(null);
        }
      }
    } catch (error) {
      console.error('Delete error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Upload Section */}
      <section style={{
        border: '2px dashed #d1d5db',
        borderRadius: '8px',
        padding: '24px',
        marginBottom: '32px',
        backgroundColor: '#f9fafb'
      }}>
        <h2 style={{ 
          fontSize: '1.25rem',
          marginBottom: '16px',
          fontWeight: '600'
        }}>
          Upload SQLite Database to R2
        </h2>
        
        <div style={{ marginBottom: '16px' }}>
          <input
            type="file"
            accept=".db,.sqlite,.sqlite3"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            style={{ marginBottom: '8px' }}
          />
          {uploadFile && (
            <div style={{ fontSize: '14px', color: '#6b7280' }}>
              Selected: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(2)} KB)
            </div>
          )}
        </div>

        <div style={{ marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Database name (optional)"
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
            style={{
              width: '300px',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={!uploadFile || loading}
          style={{
            padding: '8px 16px',
            backgroundColor: uploadFile && !loading ? '#3b82f6' : '#9ca3af',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: uploadFile && !loading ? 'pointer' : 'not-allowed',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          {loading ? 'Uploading...' : 'Upload to R2'}
        </button>
      </section>

      {/* Database List */}
      <section style={{ marginBottom: '32px' }}>
        <div style={{ 
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          <h2 style={{ 
            fontSize: '1.25rem',
            fontWeight: '600'
          }}>
            Available Databases in R2
          </h2>
          <button
            onClick={fetchDatabases}
            disabled={loading}
            style={{
              padding: '6px 12px',
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Refresh
          </button>
        </div>

        {databases.length === 0 ? (
          <div style={{
            padding: '24px',
            textAlign: 'center',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
            color: '#6b7280'
          }}>
            No databases uploaded yet
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gap: '12px',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
          }}>
            {databases.map((db) => (
              <div
                key={db.name}
                style={{
                  padding: '16px',
                  border: selectedDb === db.name ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                  borderRadius: '8px',
                  backgroundColor: selectedDb === db.name ? '#eff6ff' : 'white',
                  cursor: 'pointer'
                }}
                onClick={() => setSelectedDb(db.name)}
              >
                <div style={{ 
                  fontWeight: '600',
                  marginBottom: '8px'
                }}>
                  {db.name}
                </div>
                <div style={{ 
                  fontSize: '14px',
                  color: '#6b7280',
                  marginBottom: '4px'
                }}>
                  Size: {(db.size / 1024).toFixed(2)} KB
                </div>
                <div style={{ 
                  fontSize: '14px',
                  color: '#6b7280',
                  marginBottom: '12px'
                }}>
                  Uploaded: {new Date(db.uploaded).toLocaleString()}
                </div>
                <div style={{ 
                  display: 'flex',
                  gap: '8px'
                }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedDb(db.name);
                    }}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    Open
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(db.name);
                    }}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* SQLite Query Interface */}
      {selectedDb && (
        <SQLiteR2Loader
          dbUrl={`/api/sqlite/db/${selectedDb}`}
          wasmUrl="/wasm/sqlite3.wasm"
        />
      )}
    </div>
  );
};