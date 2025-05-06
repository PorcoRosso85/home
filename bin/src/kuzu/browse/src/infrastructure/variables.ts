/**
 * アプリケーション全体で使用する変数
 * @deprecated 代わりに common/infrastructure/variables.ts を使用してください
 */

import { DB_CONNECTION as GLOBAL_DB_CONNECTION } from '../../../common/infrastructure/variables';

// データベース接続（グローバル変数）
export const DB_CONNECTION = GLOBAL_DB_CONNECTION;
