import { SQLiteR2Simple } from '../components/sqlite-r2-simple';

export default async function SQLiteR2TestPage() {
  return (
    <div style={{ 
      padding: '24px',
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, sans-serif'
    }}>
      <h1>SQLite R2 Integration Test</h1>
      <p>This page tests loading SQLite databases from R2 storage.</p>
      
      <SQLiteR2Simple />
      
      <div style={{
        marginTop: '32px',
        padding: '16px',
        backgroundColor: '#f3f4f6',
        borderRadius: '8px',
        fontSize: '14px'
      }}>
        <h3>Test Instructions:</h3>
        <ol>
          <li>The test.db database should be listed above</li>
          <li>Click on it to load the database</li>
          <li>Check the browser console for load confirmation</li>
          <li>The database contains users and products tables</li>
        </ol>
      </div>
    </div>
  );
}

export const getConfig = async () => {
  return {
    render: 'dynamic',
  } as const;
};