/**
 * LocationURI機能専用型定義
 * CONVENTION.yaml準拠: 個別Tagged Union実装
 */

import type { NodeData } from '../../domain/coreTypes';

// LocationURI取得成功型
export type LocationUrisSuccess = {
  data: NodeData[];
};

// LocationURI取得エラー型
export type LocationUrisError = {
  code: string;
  message: string;
};

// LocationURI機能の結果型（Tagged Union）
export type LocationUrisResult = LocationUrisSuccess | LocationUrisError;

// LocationURI機能の入力型
export type LocationUrisInput = {
  dbConnection: any;
  selectedVersionId: string;
};
