/**
 * Application Layer - ユースケースとアプリケーションロジック
 * ドメインとインフラストラクチャを組み合わせる
 */

import { createPingQuery, validatePingResponse, formatPingResult } from './domain.js'
import { initializeKuzu, executeQuery } from './infrastructure.js'

/**
 * ping確認のユースケース
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const executePingUseCase = async () => {
  let kuzuConnection = null
  
  try {
    // インフラ層: Kuzu初期化
    kuzuConnection = await initializeKuzu()
    
    // ドメイン層: クエリ生成
    const query = createPingQuery()
    
    // インフラ層: クエリ実行
    const result = await executeQuery(kuzuConnection.conn, query)
    
    // ドメイン層: 結果検証
    const isValid = validatePingResponse(result)
    
    if (!isValid) {
      throw new Error('Invalid ping response')
    }
    
    // ドメイン層: 結果フォーマット
    const formattedResult = formatPingResult(result)
    
    return {
      success: true,
      message: `ping確認OK: ${formattedResult}`
    }
    
  } catch (error) {
    console.error('[Application] エラー:', error)
    return {
      success: false,
      message: `エラー: ${error.message}`
    }
    
  } finally {
    // クリーンアップ
    if (kuzuConnection) {
      await kuzuConnection.close()
    }
  }
}