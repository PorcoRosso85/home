import { FileSystemReader } from "../../infrastructure/fileSystemReader.ts";

/**
 * 型の依存関係を表すインターフェース
 */
export interface TypeDependency {
  name: string;
  metaSchema: string;
  path: string;
  dependencies: TypeDependency[];
}

/**
 * 型の依存関係を解析するサービスクラス
 */
export class TypeDependencyService {
  private fileReader: FileSystemReader;
  private schemaDir: string;
  private visitedTypes: Set<string>;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイル読み込みオブジェクト
   * @param schemaDir スキーマファイルが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, schemaDir: string = "./data/generated") {
    this.fileReader = fileReader;
    this.schemaDir = schemaDir;
    this.visitedTypes = new Set<string>();
  }

  /**
   * 型の依存関係を再帰的に取得する
   * 
   * @param typeName 型の名前
   * @param metaSchema メタスキーマの名前
   * @returns 型の依存関係ツリー
   */
  async getDependencies(typeName: string, metaSchema: string): Promise<TypeDependency