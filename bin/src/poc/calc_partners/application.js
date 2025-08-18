/**
 * Application Layer - ユースケースとアプリケーションロジック
 * ドメインとインフラストラクチャを組み合わせる
 */

import { validatePingResponse, formatPingResult } from './domain.js'
import { initializeKuzu, executeQuery } from './infrastructure.js'
import { loadQuery } from './infrastructure/cypherLoader.js'
import { log } from './log.js'

/**
 * ping確認のユースケース
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const executePingUseCase = async () => {
  let kuzuConnection = null
  
  try {
    // インフラ層: Kuzu初期化
    kuzuConnection = await initializeKuzu()
    
    // cypherLoaderでクエリを動的ロード
    const queryResult = await loadQuery('dql', 'ping')
    
    if (!queryResult.success) {
      log('ERROR', {
        uri: '/application',
        message: 'Failed to load ping query',
        error: queryResult.error
      })
      return {
        success: false,
        message: queryResult.error
      }
    }
    
    const query = queryResult.data
    log('INFO', {
      uri: '/application',
      message: 'Loaded ping query from file'
    })
    
    // インフラ層: クエリ実行
    const result = await executeQuery(kuzuConnection.conn, query)
    
    // ドメイン層: 結果検証
    const isValid = validatePingResponse(result)
    
    if (!isValid) {
      // 規約準拠: throwではなくResult型で返す
      return {
        success: false,
        message: 'Invalid ping response'
      }
    }
    
    // ドメイン層: 結果フォーマット
    const formattedResult = formatPingResult(result)
    
    return {
      success: true,
      message: `ping確認OK: ${formattedResult}`
    }
    
  } catch (error) {
    log('ERROR', {
      uri: '/application',
      message: 'Error in executePingUseCase',
      error: error.message
    })
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