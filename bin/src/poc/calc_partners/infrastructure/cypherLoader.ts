/**
 * Cypherクエリローダー
 * .cypherファイルを動的に読み込み、キャッシュ管理を行う
 */

import { log } from '../log.js'

// Result type pattern for consistent error handling
export interface QueryResult {
  success: true
  data: string
}

export interface QueryError {
  success: false
  error: string
}

export type LoadQueryResult = QueryResult | QueryError

// Cache information type
interface CacheInfo {
  size: number
  keys: string[]
}

// Valid query categories
type QueryCategory = 'ddl' | 'dql' | 'dml'

// クエリキャッシュ（メモリ内保持）
const queryCache = new Map<string, string>()

/**
 * Cypherクエリを動的にロード
 * @param category - クエリカテゴリ (ddl, dql, dml)
 * @param name - クエリ名（拡張子なし）
 * @returns Promise<LoadQueryResult>
 */
export const loadQuery = async (category: QueryCategory, name: string): Promise<LoadQueryResult> => {
  const cacheKey = `${category}/${name}`
  
  // キャッシュチェック
  if (queryCache.has(cacheKey)) {
    log('DEBUG', {
      uri: '/infrastructure/cypherLoader',
      message: `Cache hit for ${cacheKey}`
    })
    const cachedData = queryCache.get(cacheKey)!
    return {
      success: true,
      data: cachedData
    }
  }
  
  try {
    log('INFO', {
      uri: '/infrastructure/cypherLoader',
      message: `Loading query: ${cacheKey}`
    })
    
    // 動的import with ?raw to get text content
    const module = await import(`../queries/${category}/${name}.cypher?raw`) as { default: string }
    const queryContent = module.default
    
    // キャッシュに保存
    queryCache.set(cacheKey, queryContent)
    
    log('INFO', {
      uri: '/infrastructure/cypherLoader',
      message: `Query loaded successfully: ${cacheKey}`
    })
    
    return {
      success: true,
      data: queryContent
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    
    log('ERROR', {
      uri: '/infrastructure/cypherLoader',
      message: `Failed to load query: ${cacheKey}`,
      error: errorMessage
    })
    
    return {
      success: false,
      error: `Failed to load query ${cacheKey}: ${errorMessage}`
    }
  }
}

/**
 * キャッシュをクリア
 */
export const clearCache = (): void => {
  queryCache.clear()
  log('INFO', {
    uri: '/infrastructure/cypherLoader',
    message: 'Query cache cleared'
  })
}

/**
 * キャッシュ状態を取得
 * @returns キャッシュ情報
 */
export const getCacheInfo = (): CacheInfo => {
  return {
    size: queryCache.size,
    keys: Array.from(queryCache.keys())
  }
}