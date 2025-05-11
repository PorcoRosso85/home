export async function executeQuery(
  conn: any,
  queryName: string,
  params: Record<string, any>
): Promise<any> {
  // リポジトリファクトリー経由で実行環境に最適なリポジトリを取得
  const { createQueryRepository } = await import('../../../../query/infrastructure/factories/repositoryFactory');
  const repository = await createQueryRepository();
  return repository.executeQuery(conn, queryName, params);
}
