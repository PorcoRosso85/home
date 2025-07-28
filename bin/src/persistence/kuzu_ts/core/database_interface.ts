// KuzuDB操作のインターフェース定義
// Contract Serviceはこのインターフェースに依存し、実装詳細から分離

export interface IDatabase {
  close(): void;
}

export interface IConnection {
  query(statement: string, params?: Record<string, any>): Promise<IQueryResult>;
}

export interface IQueryResult {
  getAll(): Promise<Array<Record<string, any>>>;
}

export interface IDatabaseFactory {
  createDatabase(path: string, options?: DatabaseOptions): Promise<IDatabase>;
  createConnection(db: IDatabase): Promise<IConnection>;
}

export interface DatabaseOptions {
  testUnique?: boolean;
}