/**
 * 階層型トレーサビリティモデル - DML呼び出しユーティリティ
 * 
 * このファイルはDMLファイル（.cypher）を名前で呼び出し、必要なパラメータを渡すための
 * ユーティリティ関数を提供します。
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

/**
 * DMLファイルを実行する関数
 * @param conn データベース接続オブジェクト
 * @param dmlFileName 実行するDMLファイル名（.cypherを含む）
 * @param params クエリに渡すパラメータ
 * @returns クエリ実行結果
 */
export async function callDml(
  conn: any,
  dmlFileName: string,
  params: Record<string, any> = {}
): Promise<any> {
  try {
    console.log(`DMLファイル実行: ${dmlFileName}`);
    
    // DMLファイルの完全パスを構築
    const dmlFilePath = path.resolve(
      Deno.cwd(),
      `/home/nixos/bin/src/kuzu/query/tests/dml/${dmlFileName}`
    );
    
    // ファイルが存在するか確認
    try {
      await Deno.stat(dmlFilePath);
    } catch (error) {
      throw new Error(`DMLファイルが見つかりません: ${dmlFilePath}`);
    }
    
    // ファイルを読み込む
    const content = await Deno.readTextFile(dmlFilePath);
    
    // パラメータを適用したクエリを作成
    const processedQueries = processQueriesWithParams(content, params);
    
    console.log(`クエリを実行中... (${processedQueries.length}個のクエリ)`);
    
    const results = [];
    for (const query of processedQueries) {
      try {
        const result = await conn.query(query);
        results.push(result);
      } catch (error) {
        console.error(`クエリ実行エラー: ${query}`);
        console.error(`エラー詳細: ${error.message}`);
        throw error;
      }
    }
    
    console.log(`DMLファイルの実行が完了しました: ${dmlFileName}`);
    
    // 複数のクエリがある場合は結果の配列、1つの場合は単一の結果を返す
    return results.length === 1 ? results[0] : results;
    
  } catch (error) {
    console.error(`DMLファイルの実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

/**
 * 名前付きDMLクエリを実行する関数
 * @param conn データベース接続オブジェクト
 * @param dmlFileName 実行するDMLファイル名（.cypherを含む）
 * @param queryName 実行するクエリ名
 * @param params クエリに渡すパラメータ
 * @returns クエリ実行結果
 */
export async function callNamedDml(
  conn: any,
  dmlFileName: string,
  queryName: string,
  params: Record<string, any> = {}
): Promise<any> {
  try {
    console.log(`名前付きDMLクエリ実行: ${dmlFileName} -> ${queryName}`);
    
    // DMLファイルの完全パスを構築
    // 注: queries(旧)、dql(新)ディレクトリも検索する
    let dmlFilePath = path.resolve(
      Deno.cwd(),
      `/home/nixos/bin/src/kuzu/query/tests/dml/${dmlFileName}`
    );
    
    // ファイルが存在するか確認
    let fileExists = false;
    try {
      await Deno.stat(dmlFilePath);
      fileExists = true;
    } catch {
      // dmlディレクトリになければdqlディレクトリを試す
      dmlFilePath = path.resolve(
        Deno.cwd(),
        `/home/nixos/bin/src/kuzu/query/tests/dql/${dmlFileName}`
      );
      
      try {
        await Deno.stat(dmlFilePath);
        fileExists = true;
      } catch {
        // dqlディレクトリになければqueries(旧)ディレクトリを試す
        dmlFilePath = path.resolve(
          Deno.cwd(),
          `/home/nixos/bin/src/kuzu/query/tests/queries/${dmlFileName}`
        );
        
        try {
          await Deno.stat(dmlFilePath);
          fileExists = true;
        } catch {
          throw new Error(`DMLファイルが見つかりません: ${dmlFileName}`);
        }
      }
    }
    
    // ファイルを読み込む
    const content = await Deno.readTextFile(dmlFilePath);
    
    // クエリ名のマーカーを使ってクエリを検索
    const query = extractNamedQuery(content, queryName);
    
    if (!query) {
      throw new Error(`クエリ名 "${queryName}" は見つかりませんでした: ${dmlFileName}`);
    }
    
    // パラメータを適用
    const processedQuery = applyParamsToQuery(query, params);
    
    // クエリを実行
    console.log(`クエリを実行: ${processedQuery}`);
    const result = await conn.query(processedQuery);
    
    console.log(`クエリの実行が完了しました: ${queryName}`);
    return result;
    
  } catch (error) {
    console.error(`名前付きDMLクエリの実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

/**
 * 特定のパスからすべてのDMLファイルを取得する関数
 * @returns 利用可能なDMLファイル名の配列
 */
export async function listAvailableDmls(): Promise<string[]> {
  const dmlDir = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/dml");
  
  try {
    const files = [];
    for await (const entry of Deno.readDir(dmlDir)) {
      if (entry.isFile && entry.name.endsWith('.cypher')) {
        files.push(entry.name);
      }
    }
    return files;
  } catch (error) {
    console.error(`DMLファイルの一覧取得中にエラーが発生しました: ${error.message}`);
    return [];
  }
}

/**
 * DMLファイル内の名前付きクエリをすべて取得する関数
 * @param dmlFileName DMLファイル名
 * @returns クエリ名の配列
 */
export async function listNamedQueries(dmlFileName: string): Promise<string[]> {
  try {
    const dmlFilePath = path.resolve(
      Deno.cwd(),
      `/home/nixos/bin/src/kuzu/query/tests/dml/${dmlFileName}`
    );
    
    const content = await Deno.readTextFile(dmlFilePath);
    const lines = content.split("\n");
    const queryNames = [];
    
    const namePattern = /\/\/\s*@name:\s*(\w+)/;
    
    for (const line of lines) {
      const match = line.match(namePattern);
      if (match && match[1]) {
        queryNames.push(match[1]);
      }
    }
    
    return queryNames;
  } catch (error) {
    console.error(`名前付きクエリの一覧取得中にエラーが発生しました: ${error.message}`);
    return [];
  }
}

// ヘルパー関数 - ファイル内容からクエリを抽出して前処理する
function processQueriesWithParams(
  content: string,
  params: Record<string, any>
): string[] {
  // コメント行を除去し、セミコロンで分割
  const queries = content
    .split("\n")
    .filter(line => !line.trim().startsWith("//")) // コメント行を除去
    .join("\n")
    .split(";")
    .map(q => q.trim())
    .filter(q => q !== "");
  
  // 各クエリにパラメータを適用
  return queries.map(query => applyParamsToQuery(query, params));
}

// ヘルパー関数 - クエリにパラメータを適用
function applyParamsToQuery(
  query: string,
  params: Record<string, any>
): string {
  let processedQuery = query;
  
  for (const [key, value] of Object.entries(params)) {
    // 値の型に応じた処理
    let paramValue: string;
    
    if (value === null) {
      paramValue = "NULL";
    } else if (typeof value === 'string') {
      // 文字列はエスケープ処理してシングルクォートで囲む
      paramValue = `'${value.replace(/'/g, "\\'")}'`;
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      // 数値と真偽値はそのまま文字列化
      paramValue = String(value);
    } else if (Array.isArray(value)) {
      // 配列は各要素を処理して角括弧で囲む
      const elements = value.map(item => {
        if (typeof item === 'string') {
          return `'${item.replace(/'/g, "\\'")}'`;
        }
        return String(item);
      });
      paramValue = `[${elements.join(', ')}]`;
    } else if (typeof value === 'object') {
      // オブジェクトはJSON文字列化
      paramValue = JSON.stringify(value);
    } else {
      // その他の型は文字列化
      paramValue = String(value);
    }
    
    // $param_name プレースホルダを置換
    const regex = new RegExp(`\\$${key}\\b`, 'g');
    processedQuery = processedQuery.replace(regex, paramValue);
  }
  
  return processedQuery;
}

// ヘルパー関数 - 名前付きクエリを抽出
function extractNamedQuery(
  content: string,
  queryName: string
): string | null {
  const marker = `// @name: ${queryName}`;
  const lines = content.split("\n");
  let queryFound = false;
  let query = "";
  
  for (const line of lines) {
    if (line.trim() === marker) {
      queryFound = true;
      continue;
    }
    
    if (queryFound) {
      // 次のマーカーが見つかったら終了
      if (line.trim().startsWith("// @name:")) {
        break;
      }
      
      // コメント行は無視
      if (!line.trim().startsWith("//")) {
        query += line + "\n";
      }
    }
  }
  
  return queryFound ? query.trim() : null;
}
