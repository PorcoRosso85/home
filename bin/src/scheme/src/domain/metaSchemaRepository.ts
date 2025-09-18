import { MetaSchema } from "./metaSchema.ts";

/**
 * メタスキーマリポジトリのインターフェース
 */
export interface MetaSchemaRepository {
  /**
   * メタスキーマをIDで検索
   * 
   * @param id メタスキーマID
   * @returns メタスキーマまたはundefined（存在しない場合）
   */
  findById(id: string): Promise<MetaSchema | undefined>;
  
  /**
   * メタスキーマをタイトルで検索
   * 
   * @param title メタスキーマのタイトル
   * @returns メタスキーマまたはundefined（存在しない場合）
   */
  findByTitle(title: string): Promise<MetaSchema | undefined>;
  
  /**
   * 部分文字列を含むメタスキーマIDを検索
   * 
   * @param partialId 部分的なID
   * @returns 部分一致するIDの配列
   */
  findSimilarIds(partialId: string): Promise<string[]>;
  
  /**
   * 全てのメタスキーマIDを取得
   * 
   * @returns 登録されている全メタスキーマIDの配列
   */
  getAllIds(): Promise<string[]>;
  
  /**
   * メタスキーマを保存
   * 
   * @param metaSchema 保存するメタスキーマ
   */
  save(metaSchema: MetaSchema): Promise<void>;
}
