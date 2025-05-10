import type { LocationUri } from '../../../query/domain/uriTypes';
import type { TreeNodeData } from '../interface/components/TreeNode';
import { buildDynamicTree } from './uriParser';

// グローバル定義（TypeScript用）
declare global {
  interface Window {
    kuzu: any; // Kuzuモジュールのみグローバルに保持
  }
}

/**
 * KuzuDBからLocationUri一覧を取得
 */
export async function fetchLocationUris(): Promise<LocationUri[]> {
  try {
    // Kuzuモジュールが初期化されていることを確認
    if (!window.kuzu) {
      console.error('✗ Kuzuモジュールが初期化されていません');
      throw new Error('Kuzuモジュールが初期化されていません');
    }

    console.log('✓ Kuzuモジュール確認済み');

    // データベースと接続を作成
    console.log('✓ データベース接続を新規作成...');
    const db = new window.kuzu.Database("");
    const conn = new window.kuzu.Connection(db);

    try {
      // DQLディレクトリのクエリファイルを使用
      const queryPath = '/dql/fetch_all_locationuris.cypher';
      const response = await fetch(queryPath);
      if (!response.ok) {
        console.error(`✗ クエリファイルの読み込みに失敗: ${response.status} ${response.statusText}`);
        throw new Error(`クエリファイルの読み込みに失敗: ${response.status} ${response.statusText}`);
      }

      const queryText = await response.text();
      console.log('✓ クエリファイル読み込み成功');
      console.log('実行するクエリ:', queryText);

      // クエリを実行
      console.log('✓ クエリ実行開始...');
      const result = await conn.query(queryText);
      const data = await result.getAllObjects();
      console.log('✓ クエリ実行完了');
      console.log('クエリ結果:', data);
      
      // 結果を閉じる（重要！）
      await result.close();

      // LocationUriの型に変換
      const locationUris: LocationUri[] = data.map((row: any) => ({
        uri_id: row.uri_id,
        scheme: row.scheme,
        authority: row.authority || '',
        path: row.path,
        fragment: row.fragment || '',
        query: row.query || ''
      }));

      console.log(`✓ 変換完了: ${locationUris.length}件のLocationUriを取得`);
      return locationUris;
    } finally {
      // 接続とデータベースを必ず閉じる
      console.log('✓ データベース接続をクリーンアップ...');
      try {
        await conn.close();
        console.log('✓ 接続をクローズしました');
      } catch (e) {
        console.error('✗ 接続のクローズエラー:', e);
      }
      
      try {
        await db.close();
        console.log('✓ データベースをクローズしました');
      } catch (e) {
        console.error('✗ データベースのクローズエラー:', e);
      }
    }
  } catch (error) {
    console.error('✗ fetchLocationUris エラー:', error);
    console.error('エラー詳細:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    });
    throw error;
  }
}

/**
 * LocationUriからツリーデータを構築
 */
export async function fetchAndBuildTree(): Promise<TreeNodeData[]> {
  const locationUris = await fetchLocationUris();
  return buildDynamicTree(locationUris);
}

/**
 * 特定のスキームのLocationUriを取得
 */
export async function fetchLocationUrisByScheme(scheme: string): Promise<LocationUri[]> {
  const allUris = await fetchLocationUris();
  return allUris.filter(uri => uri.scheme === scheme);
}
