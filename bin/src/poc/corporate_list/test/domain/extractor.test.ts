/**
 * Tests for company name extractor
 */

import { test } from 'node:test'
import { strict as assert } from 'node:assert'
import { extractCompanyName, extractAllCompanyNames, containsCompanyName } from '../../src/domain/extractor.js'

test('Company Name Extractor', async (t) => {
  await t.test('extractCompanyName', async (t) => {
    await t.test('should extract company name with 株式会社 prefix', () => {
      const text = '株式会社テスト企業が新サービスを発表'
      const result = extractCompanyName(text)
      assert.strictEqual(result, '株式会社テスト企業')
    })

    await t.test('should extract company name with 株式会社 suffix', () => {
      const text = 'テスト企業株式会社が新サービスを発表'
      const result = extractCompanyName(text)
      assert.strictEqual(result, 'テスト企業株式会社')
    })

    await t.test('should return null for text without company name', () => {
      const text = '新しいサービスが発表されました'
      const result = extractCompanyName(text)
      assert.strictEqual(result, null)
    })

    await t.test('should return null for empty text', () => {
      const result = extractCompanyName('')
      assert.strictEqual(result, null)
    })

    await t.test('should return null for null input', () => {
      const result = extractCompanyName(null as any)
      assert.strictEqual(result, null)
    })

    await t.test('should return first match when multiple patterns exist', () => {
      const text = '株式会社テスト企業とサンプル企業株式会社が提携'
      const result = extractCompanyName(text)
      assert.strictEqual(result, '株式会社テスト企業')
    })
  })

  await t.test('extractAllCompanyNames', async (t) => {
    await t.test('should extract multiple company names', () => {
      const text = '株式会社テスト企業とサンプル企業株式会社が提携'
      const result = extractAllCompanyNames(text)
      assert.deepStrictEqual(result, ['株式会社テスト企業', 'サンプル企業株式会社'])
    })

    await t.test('should return empty array for text without company names', () => {
      const text = '新しいサービスが発表されました'
      const result = extractAllCompanyNames(text)
      assert.deepStrictEqual(result, [])
    })

    await t.test('should remove duplicates', () => {
      const text = '株式会社テスト企業、株式会社テスト企業が発表'
      const result = extractAllCompanyNames(text)
      assert.deepStrictEqual(result, ['株式会社テスト企業'])
    })
  })

  await t.test('containsCompanyName', async (t) => {
    await t.test('should return true when text contains company name', () => {
      const text = '株式会社テスト企業が新サービスを発表'
      const result = containsCompanyName(text)
      assert.strictEqual(result, true)
    })

    await t.test('should return false when text does not contain company name', () => {
      const text = '新しいサービスが発表されました'
      const result = containsCompanyName(text)
      assert.strictEqual(result, false)
    })
  })
})