/**
 * Cypherクエリローダー
 * .cypherファイルを動的に読み込み、キャッシュ管理を行う
 */

import { log } from '../log.js'

// クエリキャッシュ（メモリ内保持）
const queryCache = new Map()

/**
 * Cypherクエリを動的にロード
 * @param {string} category - クエリカテゴリ (ddl, dql, dml)
 * @param {string} name - クエリ名（拡張子なし）
 * @returns {Promise<{success: boolean, data?: string, error?: string}>}
 */
export const loadQuery = async (category, name) => {
  const cacheKey = `${category}/${name}`
  
  // キャッシュチェック
  if (queryCache.has(cacheKey)) {
    log('DEBUG', {
      uri: '/infrastructure/cypherLoader',
      message: `Cache hit for ${cacheKey}`
    })
    return {
      success: true,
      data: queryCache.get(cacheKey)
    }
  }
  
  try {
    log('INFO', {
      uri: '/infrastructure/cypherLoader',
      message: `Loading query: ${cacheKey}`
    })
    
    // 動的import with ?raw to get text content
    const module = await import(`../queries/${category}/${name}.cypher?raw`)
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
    log('ERROR', {
      uri: '/infrastructure/cypherLoader',
      message: `Failed to load query: ${cacheKey}`,
      error: error.message
    })
    
    return {
      success: false,
      error: `Failed to load query ${cacheKey}: ${error.message}`
    }
  }
}

/**
 * キャッシュをクリア
 */
export const clearCache = () => {
  queryCache.clear()
  log('INFO', {
    uri: '/infrastructure/cypherLoader',
    message: 'Query cache cleared'
  })
}

/**
 * キャッシュ状態を取得
 * @returns {Object} キャッシュ情報
 */
export const getCacheInfo = () => {
  return {
    size: queryCache.size,
    keys: Array.from(queryCache.keys())
  }
}