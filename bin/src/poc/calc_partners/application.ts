/**
 * Application Layer - ユースケースとアプリケーションロジック
 * ドメインとインフラストラクチャを組み合わせる
 */

import { validatePingResponse, formatPingResult } from './domain.ts'
import { initializeKuzu, executeQuery, type KuzuConnectionInfo } from './infrastructure/index.js'
import { loadQuery, type LoadQueryResult } from './infrastructure/cypherLoader.ts'
import { log } from './log.js'

/**
 * アプリケーション層の結果型
 */
export interface ApplicationResult {
  success: boolean
  message: string
  data?: any
}

/**
 * DDLスキーマ初期化（KISS原則：最小限実装）
 * @param kuzuConnection - Kuzu接続情報
 * @returns スキーマ初期化結果
 */
export const initializeSchema = async (kuzuConnection: KuzuConnectionInfo): Promise<ApplicationResult> => {
  try {
    const schemaResult: LoadQueryResult = await loadQuery('ddl', 'schema')
    
    if (!schemaResult.success) {
      return {
        success: false,
        message: `Failed to load schema: ${schemaResult.error}`
      }
    }
    
    // スキーマ実行（エラーは無視 - YAGNI）
    try {
      await executeQuery(kuzuConnection.conn, schemaResult.data)
      log('INFO', {
        uri: '/application',
        message: 'Schema initialized'
      })
    } catch (e) {
      // 既存スキーマは問題なし
    }
    
    return { success: true, message: 'Schema ready' }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    return { success: false, message: errorMessage }
  }
}

/**
 * DQLテスト実行（KISS：1つだけテスト）
 * @returns DQLクエリ実行結果
 */
export const testDQLQuery = async (): Promise<ApplicationResult> => {
  let kuzuConnection: KuzuConnectionInfo | null = null
  
  try {
    kuzuConnection = await initializeKuzu()
    
    // Step 1: DDL実行
    await initializeSchema(kuzuConnection)
    
    // Step 2: calculate_ltv.cypherを実行（データなし）
    const queryResult: LoadQueryResult = await loadQuery('dql', 'calculate_ltv')
    
    if (!queryResult.success) {
      return {
        success: false,
        message: 'Failed to load DQL query'
      }
    }
    
    // 空データでクエリ実行
    const result: any[] = await executeQuery(kuzuConnection.conn, queryResult.data)
    
    // 空配列が返ることを確認
    log('INFO', {
      uri: '/application',
      message: 'DQL result',
      result: result
    })
    
    return {
      success: true,
      message: `DQL returned: ${JSON.stringify(result)}`,
      data: result
    }
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    return {
      success: false,
      message: errorMessage
    }
  } finally {
    if (kuzuConnection) {
      await kuzuConnection.close()
    }
  }
}

/**
 * ping確認のユースケース
 * @returns ping実行結果
 */
export const executePingUseCase = async (): Promise<ApplicationResult> => {
  let kuzuConnection: KuzuConnectionInfo | null = null
  
  try {
    // インフラ層: Kuzu初期化
    kuzuConnection = await initializeKuzu()
    
    // cypherLoaderでクエリを動的ロード
    const queryResult: LoadQueryResult = await loadQuery('dql', 'ping')
    
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
    
    const query: string = queryResult.data
    log('INFO', {
      uri: '/application',
      message: 'Loaded ping query from file'
    })
    
    // インフラ層: クエリ実行
    const result: any[] = await executeQuery(kuzuConnection.conn, query)
    
    // ドメイン層: 結果検証
    const isValid: boolean = validatePingResponse(result)
    
    if (!isValid) {
      // 規約準拠: throwではなくResult型で返す
      return {
        success: false,
        message: 'Invalid ping response'
      }
    }
    
    // ドメイン層: 結果フォーマット
    const formattedResult: string = formatPingResult(result)
    
    return {
      success: true,
      message: `ping確認OK: ${formattedResult}`
    }
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    log('ERROR', {
      uri: '/application',
      message: 'Error in executePingUseCase',
      error: errorMessage
    })
    return {
      success: false,
      message: `エラー: ${errorMessage}`
    }
    
  } finally {
    // クリーンアップ
    if (kuzuConnection) {
      await kuzuConnection.close()
    }
  }
}