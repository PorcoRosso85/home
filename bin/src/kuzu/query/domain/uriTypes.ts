/**
 * LocationURIエンティティに準拠した型定義
 * @see /home/nixos/bin/src/kuzu/query/dml/location_uri.json
 */
export type LocationUri = {
  uri_id: string;          // URI識別子（主キー）
  scheme: string;          // URIスキーム（例: http, file）
  authority: string;       // URIオーソリティ部分
  path: string;            // URIパス部分
  fragment: string;        // URIフラグメント部分
  query: string;           // URIクエリ部分
}

/**
 * URI解析結果の型
 */
export type ParsedUri = LocationUri & {
  isValid: boolean;
  error?: string;
}
