export async function executeQuery(
  conn: any,
  queryName: string,
  params: Record<string, any>
): Promise<any> {
  // ブラウザー用のDMLクエリ実行関数をインポート
  const { executeQuery: executeDmlQuery } = await import('../../../../query/dmlGeneratorBrowser');
  return executeDmlQuery(conn, queryName, params);
}
