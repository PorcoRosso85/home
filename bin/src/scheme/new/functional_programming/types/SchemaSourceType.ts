/**
 * スキーマ参照のソース種別
 * 
 * スキーマデータがどこから取得されるかを示す列挙型です。
 * 
 * @example
 * import { SchemaSourceType } from './SchemaSourceType';
 * 
 * // ローカルファイルシステムからのスキーマ参照
 * const sourceType = SchemaSourceType.LOCAL;
 * 
 * // Webからのスキーマ参照 
 * const webSource = SchemaSourceType.WEB;
 * 
 * // 条件に基づいてソース種別を選択
 * function getSourceType(isRemote: boolean): SchemaSourceType {
 *   return isRemote ? SchemaSourceType.WEB : SchemaSourceType.LOCAL;
 * }
 */
export enum SchemaSourceType {
  /** ローカルファイルシステムからのスキーマ参照 */
  LOCAL = 'local',
  
  /** Webサーバーからのスキーマ参照 */
  WEB = 'web',
  
  /** コンテンツ配信ネットワークからのスキーマ参照 */
  CDN = 'cdn',
  
  /** Origin Private File System からのスキーマ参照 */
  OPFS = 'opfs',
}
