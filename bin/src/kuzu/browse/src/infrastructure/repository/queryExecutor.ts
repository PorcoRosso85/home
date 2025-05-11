export async function executeQuery(
  conn: any,
  queryName: string,
  params: Record<string, any>
): Promise<any> {
  // リポジトリファクトリー経由で実行環境に最適なリポジトリを取得
  const { createQueryRepository } = await import('../../../../query/infrastructure/factories/repositoryFactory');
  const repository = await createQueryRepository();
  // 後方互換性のため、DQLをデフォルトとする
  return repository.executeQuery(conn, queryName, 'dql', params);
}

/**
 * DDL系クエリを実行する関数
 */
export async function executeDDLQuery(
  conn: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<any> {
  const { createQueryRepository } = await import('../../../../query/infrastructure/factories/repositoryFactory');
  const repository = await createQueryRepository();
  return repository.executeDDLQuery(conn, queryName, params);
}

/**
 * DML系クエリを実行する関数
 */
export async function executeDMLQuery(
  conn: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<any> {
  const { createQueryRepository } = await import('../../../../query/infrastructure/factories/repositoryFactory');
  const repository = await createQueryRepository();
  return repository.executeDMLQuery(conn, queryName, params);
}

/**
 * DQL系クエリを実行する関数
 */
export async function executeDQLQuery(
  conn: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<any> {
  const { createQueryRepository } = await import('../../../../query/infrastructure/factories/repositoryFactory');
  const repository = await createQueryRepository();
  return repository.executeDQLQuery(conn, queryName, params);
}
