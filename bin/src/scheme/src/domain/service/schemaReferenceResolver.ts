import { FileSystemReader } from "../../infrastructure/fileSystemReader.ts";
import { DIRECTORIES, META_SOURCE_TYPE, META_SOURCE_CONFIG, SCHEMA_CONFIG } from "../../infrastructure/variables.ts";

/**
 * スキーマ参照のソース種別
 */
export { META_SOURCE_TYPE as SchemaSourceType };

/**
 * スキーマ参照情報
 */
export interface SchemaReference {
  typeId: string;
  metaSource: SchemaSourceType;
  metaId: string;
}

/**
 * URIベースのスキーマ参照を解決するクラス
 */
export class SchemaReferenceResolver {
  private fileReader: FileSystemReader;
  private schemaDir: string;
  private schemaCache: Map<string, any>;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイル読み込みオブジェクト
   * @param schemaDir スキーマファイルが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, schemaDir: string = DIRECTORIES.GENERATED) {
    this.fileReader = fileReader;
    this.schemaDir = schemaDir;
    this.schemaCache = new Map<string, any>();
  }

  /**
   * URIからスキーマ参照情報を解析する
   * 
   * @param uri スキーマ参照URI (例: "scheme://User/local:Struct")
   * @returns スキーマ参照情報
   */
  public parseReference(uri: string): SchemaReference | null {
    // scheme:// プロトコルのチェック
    if (!uri.startsWith(SCHEMA_CONFIG.URI_SCHEME)) {
      return null;
    }

    // URIの形式: scheme://<type-id>/<meta-source>:<meta-id>
    const path = uri.substring(SCHEMA_CONFIG.URI_SCHEME.length);
    const parts = path.split('/');
    
    if (parts.length !== 2) {
      return null;
    }

    const typeId = parts[0];
    const metaParts = parts[1].split(':');
    
    if (metaParts.length !== 2) {
      return null;
    }

    const metaSource = metaParts[0] as SchemaSourceType;
    const metaId = metaParts[1];

    // メタソースの検証
    if (!Object.values(META_SOURCE_TYPE).includes(metaSource as META_SOURCE_TYPE)) {
      return null;
    }

    return {
      typeId,
      metaSource: metaSource as META_SOURCE_TYPE,
      metaId
    };
  }

  /**
   * スキーマ参照情報から実際のスキーマを解決する
   * 
   * @param reference スキーマ参照情報
   * @returns 解決されたスキーマ
   */
  public async resolveSchema(reference: SchemaReference): Promise<any> {
    const { typeId, metaSource, metaId } = reference;
    
    // キャッシュキーを生成
    const cacheKey = `${typeId}/${metaSource}:${metaId}`;
    
    // キャッシュにあればそれを返す
    if (this.schemaCache.has(cacheKey)) {
      return this.schemaCache.get(cacheKey);
    }
    
    // メタソースに応じた読み込み処理
    let schema;
    switch (metaSource) {
      case SchemaSourceType.LOCAL:
        // ローカルスキーマの読み込み
        schema = await this.loadLocalSchema(typeId, metaId);
        break;
        
      case SchemaSourceType.WEB:
        // Webスキーマの読み込み（将来実装）
        throw new Error("Webスキーマの読み込みは未実装です");
        
      case SchemaSourceType.CDN:
        // CDNスキーマの読み込み（将来実装）
        throw new Error("CDNスキーマの読み込みは未実装です");
        
      case SchemaSourceType.OPFS:
        // OPFSスキーマの読み込み（将来実装）
        throw new Error("OPFSスキーマの読み込みは未実装です");
        
      default:
        throw new Error(`未対応のメタソース: ${metaSource}`);
    }
    
    // キャッシュに保存
    this.schemaCache.set(cacheKey, schema);
    
    return schema;
  }

  /**
   * URIから直接スキーマを解決する
   * 
   * @param uri スキーマ参照URI
   * @returns 解決されたスキーマ
   */
  public async resolveSchemaFromUri(uri: string): Promise<any> {
    const reference = this.parseReference(uri);
    if (!reference) {
      throw new Error(`無効なスキーマ参照URI: ${uri}`);
    }
    
    return this.resolveSchema(reference);
  }

  /**
   * ローカルスキーマを読み込む
   * 
   * @param typeId 型ID
   * @param metaId メタID
   * @returns 読み込まれたスキーマ
   */
  private async loadLocalSchema(typeId: string, metaId: string): Promise<any> {
    const schemaPath = `${META_SOURCE_CONFIG[META_SOURCE_TYPE.LOCAL].BASE_DIR}/${typeId}.${metaId}.schema.json`;
    try {
      return await this.fileReader.readJsonFile(schemaPath);
    } catch (error) {
      throw new Error(`スキーマの読み込みに失敗しました: ${schemaPath} - ${error.message}`);
    }
  }

  /**
   * 旧形式のファイルパス参照から新形式のURI参照に変換する
   * 
   * @param fileRef ファイルパス参照 (例: "./data/generated/User.Struct.schema.json")
   * @returns URI参照 (例: "scheme://User/local:Struct")
   */
  public convertFileRefToUri(fileRef: string): string | null {
    // ファイル名から型名とメタスキーマを抽出
    const match = fileRef.match(/([^\/]+)\.([^\/]+)\.schema\.json$/);
    if (!match) {
      return null;
    }
    
    const typeId = match[1];
    const metaId = match[2];
    
    // 新形式のURI参照を生成
    return `${SCHEMA_CONFIG.URI_SCHEME}${typeId}/${META_SOURCE_TYPE.LOCAL}:${metaId}`;
  }
}
