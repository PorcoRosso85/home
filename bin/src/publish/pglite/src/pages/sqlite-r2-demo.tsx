import { SQLiteR2Manager } from '../components/sqlite-r2-manager';

export default function SQLiteR2DemoPage() {
  return (
    <div style={{ 
      padding: '32px',
      maxWidth: '1200px',
      margin: '0 auto'
    }}>
      <h1 style={{ 
        fontSize: '2rem',
        marginBottom: '24px',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, sans-serif'
      }}>
        SQLite + R2 Demo
      </h1>
      
      <p style={{ 
        marginBottom: '32px',
        color: '#6b7280',
        lineHeight: 1.6
      }}>
        SQLiteデータベースをR2にアップロードして、ブラウザ上で直接クエリを実行できます。
        ローカル開発時は`.wrangler/state/`にデータが保存され、本番環境ではCloudflare R2を使用します。
      </p>

      <SQLiteR2Manager />
    </div>
  );
}

export const getConfig = async () => {
  return {
    render: 'dynamic',
  };
};