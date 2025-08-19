/**
 * Cypherクエリローダー
 * .cypherファイルを動的に読み込み、キャッシュ管理を行う
 */

import fs from 'node:fs'
import path from 'node:path'
// Simple console logging
const log = console.log.bind(console)

// Result type pattern for consistent error handling
export type QueryResult = {
  success: true
  data: string
}

export type QueryError = {
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
 * @returns LoadQueryResult
 */
export const loadQuery = (category: QueryCategory, name: string): LoadQueryResult => {
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
    
    // Build file path and read content synchronously
    const filePath = path.join(process.cwd(), 'queries', category, `${name}.cypher`)
    const queryContent = fs.readFileSync(filePath, 'utf-8')
    
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