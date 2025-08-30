'use client';

import { useState, useEffect } from 'react';
import { listDatabases, getDatabase } from '../server/sqlite-actions';

export const SQLiteR2Simple = () => {
  const [databases, setDatabases] = useState<any[]>([]);
  const [selectedDb, setSelectedDb] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // List databases on mount
    listDatabases().then(setDatabases);
  }, []);

  const loadDatabase = async (name: string) => {
    setLoading(true);
    try {
      const buffer = await getDatabase(name);
      console.log(`Loaded database: ${name}, size: ${buffer.byteLength} bytes`);
      // Here you would initialize sql.js with the buffer
      setSelectedDb(name);
    } catch (error) {
      console.error('Database load error:', error);
      alert(`Failed to load database: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>SQLite Databases in R2</h2>
      
      {databases.length === 0 ? (
        <p>No databases found</p>
      ) : (
        <ul>
          {databases.map(db => (
            <li key={db.name}>
              <button 
                onClick={() => loadDatabase(db.name)}
                disabled={loading}
              >
                {db.name} ({(db.size / 1024).toFixed(2)} KB)
              </button>
            </li>
          ))}
        </ul>
      )}
      
      {selectedDb && (
        <div>
          <h3>Selected: {selectedDb}</h3>
          <p>Database loaded. Ready for sql.js operations.</p>
        </div>
      )}
    </div>
  );
};