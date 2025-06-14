/**
 * バージョン機能専用型定義
 * CONVENTION.yaml準拠: 個別Tagged Union実装
 */

import type { VersionState } from '../../domain/coreTypes';

// バージョン取得成功型
export type VersionStatesSuccess = {
  data: VersionState[];
};

// バージョン取得エラー型
export type VersionStatesError = {
  code: string;
  message: string;
};

// バージョン機能の結果型（Tagged Union）
export type VersionStatesResult = VersionStatesSuccess | VersionStatesError;

// バージョン機能の入力型
export type VersionStatesInput = {
  dbConnection: any;
};
