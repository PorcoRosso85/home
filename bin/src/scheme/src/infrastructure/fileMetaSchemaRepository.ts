import { MetaSchema } from "../domain/metaSchema.ts";
import { MetaSchemaRepository } from "../domain/metaSchemaRepository.ts";
import { FileSystemReader } from "./fileSystemReader.ts";

/**
 * ファイルシステムベースのメタスキーマリポジトリ実装
 */
export class FileMetaSchemaRepository implements MetaSchemaRepository {
  private metaSchemas: Map<string, MetaSchema> = new Map();
  private fileReader: FileSystemReader;
  private metaSchemaDir: string;
  
  /**
   * コンストラクタ
   * 
   * @param fileReader ファイル読み込みオブジェクト
   * @param metaSchemaDir メタスキーマファイルが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, metaSchemaDir: string = "./data/meta") {
    this.fileReader = fileReader;
    this.metaSchemaDir = metaSchemaDir;
  }
  
  /**
   * リポジトリを初期化（メタスキーマの読み込み）
   */
  async initialize(): Promise<void> {
    try {
      // メタスキーマディレクトリからメタスキーマファイルを探索
      const metaSchemaFiles = await this.fileReader.findJsonFiles(
        this.metaSchemaDir,
        (entry) => entry.name.endsWith(".meta.json")
      );
      
      console.log(`メタスキーマディレクトリ ${this.metaSchemaDir} から ${metaSchemaFiles.length} 件のファイルを見つけました`);
      
      // 各メタスキーマファイルを読み込んでマップに格納
      for (const filePath of metaSchemaFiles) {
        try {
          const metaSchema = await this.fileReader.readJsonFile(filePath);
          if (metaSchema.title) {
            // metaSchema.typeはobjectになっている可能性があるため、
            // String型の場合は "string" に変換する
            let type = metaSchema.type;
            if (metaSchema.title === "String" && (type === "object" || !type)) {
              type = "string";
            } else if (metaSchema.title === "Struct" && (type === "object" || !type)) {
              type = "struct";
            } else if (metaSchema.title === "Function" && (type === "object" || !type)) {
              type = "function";
            }
            
            this.metaSchemas.set(metaSchema.title, {
              id: metaSchema.title,
              title: metaSchema.title,
              schema: metaSchema,
              type: type || "unknown"
            });
          }
        } catch (error) {
          console.warn(`メタスキーマファイル '${filePath}' の読み込みに失敗しました: ${error.message}`);
        }
      }
      
      console.log(`${this.metaSchemas.size} 件のメタスキーマを読み込みました`);
    } catch (error) {
      console.error(`メタスキーマリポジトリの初期化に失敗しました: ${error.message}`);
    }
  }
  
  /**
   * メタスキーマをIDで検索
   */
  async findById(id: string): Promise<MetaSchema | undefined> {
    return this.metaSchemas.get(id);
  }
  
  /**
   * メタスキーマをタイトルで検索
   */
  async findByTitle(title: string): Promise<MetaSchema | undefined> {
    return this.metaSchemas.get(title);
  }
  
  /**
   * 部分文字列を含むメタスキーマIDを検索
   */
  async findSimilarIds(partialId: string): Promise<string[]> {
    const lowerPartialId = partialId.toLowerCase();
    return Array.from(this.metaSchemas.keys())
      .filter(id => id.toLowerCase().includes(lowerPartialId));
  }
  
  /**
   * 全てのメタスキーマIDを取得
   */
  async getAllIds(): Promise<string[]> {
    return Array.from(this.metaSchemas.keys());
  }
  
  /**
   * メタスキーマを保存
   */
  async save(metaSchema: MetaSchema): Promise<void> {
    this.metaSchemas.set(metaSchema.id, metaSchema);
  }
}
