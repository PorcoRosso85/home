/**
 * KuzuDB DML Generator for Browser
 * 
 * このモジュールは、ブラウザ環境でDMLクエリを実行するためのユーティリティを提供します。
 * ファイル操作の代わりにfetchを使用します。
 */

// 型定義
type QueryResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
  available_queries?: string[];
};

/**
 * クエリファイルを検索する（ブラウザ版）
 * @param queryName 検索するクエリ名
 * @returns [成功フラグ, ファイルパスまたはエラーメッセージ]
 */
async function findQueryFile(queryName: string): Promise<[boolean, string]> {
  // 検索優先順位
  const searchPaths = [
    // 1. DMLディレクトリ内
    `/dml/${queryName}.cypher`,
    // 2. DDLディレクトリ内
    `/ddl/${queryName}.cypher`,
    // 3. クエリディレクトリ直下（互換性のため）
    `/${queryName}.cypher`
  ];
  
  // 各パスを順番に検索
  for (const path of searchPaths) {
    try {
      const response = await fetch(path);
      if (response.ok) {
        return [true, path];
      }
    } catch (e) {
      // 次のパスを試す
      continue;
    }
  }
  
  // 見つからなかった場合
  return [false, `クエリファイル '${queryName}' が見つかりませんでした`];
}

/**
 * クエリファイルの内容を読み込む（ブラウザ版）
 * @param filePath 読み込むファイルパス
 * @returns 成功時は {success: true, data: ファイル内容}、失敗時は {success: false, error: エラーメッセージ}
 */
async function readQueryFile(filePath: string): Promise<QueryResult<string>> {
  try {
    const response = await fetch(filePath);
    if (!response.ok) {
      return { success: false, error: `ファイルの読み込みに失敗しました: ${filePath} (${response.status})` };
    }
    
    const content = await response.text();
    return { success: true, data: content };
  } catch (e) {
    return { 
      success: false, 
      error: `クエリファイルの読み込みに失敗しました: ${filePath} - ${e instanceof Error ? e.message : String(e)}` 
    };
  }
}

/**
 * 利用可能なすべてのクエリ名のリストを取得する（ブラウザ版）
 * @returns 拡張子を除いたクエリファイル名のリスト（アルファベット順）
 */
export async function getAvailableQueries(): Promise<string[]> {
  const queryFiles: string[] = [];
  const directories = ['ddl', 'dml', 'dql'];
  
  for (const dir of directories) {
    try {
      const response = await fetch(`/${dir}/`);
      if (response.ok) {
        const files = await response.json();
        for (const file of files) {
          if (typeof file === 'string' && file.endsWith('.cypher')) {
            queryFiles.push(file.replace('.cypher', ''));
          }
        }
      }
    } catch (e) {
      // ディレクトリが存在しないか読み込みエラー
      console.warn(`ディレクトリ ${dir} の読み込みに失敗しました:`, e);
    }
  }
  
  // 重複を削除してソート
  return [...new Set(queryFiles)].sort();
}

/**
 * クエリ名に対応するCypherクエリを取得する（ブラウザ版）
 * @param queryName 取得するクエリ名
 * @param fallbackQuery クエリが見つからない場合のフォールバッククエリ（オプション）
 * @returns 成功時は {success: true, data: クエリ内容}、失敗時は {success: false, error: エラーメッセージ}
 */
export async function getQuery(queryName: string, fallbackQuery?: string): Promise<QueryResult<string>> {
  // 通常のクエリファイル検索
  const [found, filePath] = await findQueryFile(queryName);
  if (!found) {
    if (fallbackQuery !== undefined) {
      console.log(`INFO: クエリ '${queryName}' が見つからないため、フォールバッククエリを使用します`);
      return { success: true, data: fallbackQuery };
    }
    const available = await getAvailableQueries();
    return {
      success: false,
      error: `クエリ '${queryName}' が見つかりません`,
      available_queries: available
    };
  }
  
  // ファイルを読み込む
  return await readQueryFile(filePath);
}

/**
 * クエリ名に対応するCypherクエリを実行する（ブラウザ版）
 * @param connection データベース接続オブジェクト
 * @param queryName 実行するクエリ名
 * @param params クエリパラメータ
 * @returns 成功時は {success: true, data: 実行結果}、失敗時は {success: false, error: エラーメッセージ}
 */
export async function executeQuery(
  connection: any, 
  queryName: string, 
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  console.log(`executeQuery called: queryName=${queryName}, params=`, params);
  
  // クエリを取得
  const queryResult = await getQuery(queryName);
  if (!queryResult.success) {
    console.log(`getQuery failed:`, queryResult);
    return queryResult;
  }
  
  const query = queryResult.data!;
  console.log(`Query to execute: "${query}"`);
  console.log(`Query params:`, params);
  
  // クエリを実行
  try {
    // Kuzuのコネクションオブジェクトに応じてメソッド名を調整
    const result = await (connection.query ? connection.query(query, params) : connection.executeQuery(query, params));
    console.log(`Query executed successfully:`, result);
    return { success: true, data: result };
  } catch (e) {
    console.error(`Query execution failed:`, e);
    return { 
      success: false, 
      error: `クエリ '${queryName}' の実行に失敗しました: ${e instanceof Error ? e.message : String(e)}` 
    };
  }
}

/**
 * 成功判定ヘルパー関数
 * @param result クエリ結果
 * @returns 成功か否か
 */
export function getSuccess<T>(result: QueryResult<T>): boolean {
  return result.success === true;
}
