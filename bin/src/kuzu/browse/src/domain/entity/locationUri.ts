import type { LocationUri as QueryLocationUri, ParsedUri as QueryParsedUri } from '../../../../query/domain/uriTypes';

// クエリモジュールの型定義を再エクスポート
export type LocationUri = QueryLocationUri;
export type ParsedUri = QueryParsedUri;

// TreeNodeDataの型定義
export type TreeNodeData = {
  id: string;
  type: 'entity' | 'value';
  name: string;
  uri: string;
  properties: {
    path: string;
    isLeaf: boolean;
    locationUri?: LocationUri;
    scheme?: string;
  };
  children?: TreeNodeData[];
};
