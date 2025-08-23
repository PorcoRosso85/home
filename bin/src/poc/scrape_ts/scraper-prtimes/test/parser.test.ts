/**
 * PR Times parser functions test
 * パーサー関数の単体テスト
 */

import { test, describe } from 'node:test'
import assert from 'node:assert'
import { extractCompanyName, cleanTitle } from '../src/parser.js'

describe('PR Times Parser Functions', () => {
  
  describe('extractCompanyName', () => {
    test('should extract valid company name', () => {
      const result = extractCompanyName('株式会社テスト')
      assert.strictEqual(result, '株式会社テスト')
    })

    test('should return null for empty string', () => {
      const result = extractCompanyName('')
      assert.strictEqual(result, null)
    })

    test('should return null for whitespace only', () => {
      const result = extractCompanyName('   ')
      assert.strictEqual(result, null)
    })

    test('should return null for too short text', () => {
      const result = extractCompanyName('A')
      assert.strictEqual(result, null)
    })

    test('should trim whitespace', () => {
      const result = extractCompanyName('  株式会社テスト  ')
      assert.strictEqual(result, '株式会社テスト')
    })
  })

  describe('cleanTitle', () => {
    test('should return cleaned title within max length', () => {
      const result = cleanTitle('テストタイトル', 100)
      assert.strictEqual(result, 'テストタイトル')
    })

    test('should truncate title to max length', () => {
      const longTitle = 'とても長いタイトル'.repeat(10)
      const result = cleanTitle(longTitle, 10)
      assert.strictEqual(result.length, 10)
    })

    test('should return empty string for empty input', () => {
      const result = cleanTitle('')
      assert.strictEqual(result, '')
    })

    test('should trim whitespace', () => {
      const result = cleanTitle('  テストタイトル  ')
      assert.strictEqual(result, 'テストタイトル')
    })

    test('should use default max length when not specified', () => {
      const longTitle = 'A'.repeat(200)
      const result = cleanTitle(longTitle)
      assert.strictEqual(result.length, 100) // DEFAULT_MAX_TITLE_LENGTH
    })
  })
})