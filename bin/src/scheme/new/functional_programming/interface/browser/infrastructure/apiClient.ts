/**
 * apiClient.ts
 * 
 * サーバーAPIとの通信を行うクライアント実装
 */

import { ApiClient } from '../../../application/types/apiClient.ts';
import { CommonClient } from '../../client/types.ts';

/**
 * APIクライアントの取得
 * @returns APIクライアントインスタンス
 */
export function createApiClient(): CommonClient {
  return new ApiClient('/api/', true);
}
