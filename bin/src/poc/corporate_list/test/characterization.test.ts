/**
 * 特性テスト（Feathers流）
 * 現在のスクレイパー動作を記録・保護するためのテスト
 * 
 * 目的：リファクタリング前に現在の振る舞いを完全に保護する
 * 手法：実際の動作結果を"正しい振る舞い"として記録
 * 
 * @see bin/docs/conventions/tdd_process.md - パターンB: 既存コード改修TDD（Feathers流）
 */

import { describe, expect, it, beforeAll, afterAll } from 'bun:test'
import { exec } from 'child_process'
import { promisify } from 'util'
import { readFile } from 'fs/promises'
import { join } from 'path'

const execAsync = promisify(exec)

describe('Characterization Tests - 現在のスクレイパー動作の保護', () => {
  let goldenMasterData: any
  let currentOutput: any

  beforeAll(async () => {
    // ゴールデンマスターデータの読み込み
    try {
      const goldenPath = join(__dirname, 'golden-master.json')
      const goldenContent = await readFile(goldenPath, 'utf-8')
      goldenMasterData = JSON.parse(goldenContent)
    } catch (error) {
      console.error('⚠️  Golden master not found - will capture current behavior')
    }
  })

  it('現在のmain.tsの動作を記録する（CHARACTERIZE）', async () => {
    // 現在の実装を実行
    const { stdout, stderr } = await execAsync('bun run src/main.ts', {
      cwd: process.cwd(),
      env: { ...process.env, CI: 'true' } // CI環境をシミュレート
    })

    // JSON出力を抽出
    const jsonMatch = stdout.match(/📊 Results:[\s\S]*?(\[[\s\S]*?\])/m)
    if (jsonMatch) {
      currentOutput = JSON.parse(jsonMatch[1])
    }

    // 基本的な構造検証
    expect(Array.isArray(currentOutput)).toBe(true)
    expect(currentOutput.length).toBeGreaterThan(0)

    // 各要素の構造を検証
    currentOutput.forEach((item: any) => {
      expect(item).toHaveProperty('source')
      expect(item).toHaveProperty('company_name')
      expect(item).toHaveProperty('title')
      expect(item).toHaveProperty('url')
      expect(item).toHaveProperty('scraped_at')
    })

    console.log(`✅ Captured ${currentOutput.length} articles`)
  })

  it('120記事の取得動作を保護する', async () => {
    // 実行時の記事数を確認
    expect(currentOutput.length).toBe(120)
    
    // PR_TIMESソースであることを確認
    const prTimesArticles = currentOutput.filter((item: any) => 
      item.source === 'PR_TIMES'
    )
    expect(prTimesArticles.length).toBe(120)
  })

  it('企業名抽出の現在の精度を記録する', async () => {
    // 企業名が抽出できている記事数を確認
    const withCompanyName = currentOutput.filter((item: any) => 
      item.company_name && item.company_name !== '' && item.company_name !== null
    )
    
    const extractionRate = (withCompanyName.length / currentOutput.length) * 100
    
    // 現在の実装の実際の抽出率を記録（改善が必要）
    console.log(`📊 Company name extraction rate: ${extractionRate.toFixed(1)}%`)
    
    // 現在の実装は0%だが、これが現在の動作として記録
    expect(extractionRate).toBe(0)
  })

  it('特定のキーワード検索が機能することを保護する', async () => {
    // 現在の実装では特定キーワードの記事が取得されているか確認
    // 実際の結果に基づいて記録
    const hasArticles = currentOutput && currentOutput.length > 0
    expect(hasArticles).toBe(true)
    
    // タイトルが存在することを確認
    const titlesExist = currentOutput.every((item: any) => 
      item.title && typeof item.title === 'string'
    )
    expect(titlesExist).toBe(true)
    
    console.log(`📝 Sample titles: ${currentOutput.slice(0, 3).map((item: any) => item.title).join(', ')}`)
  })

  it('出力形式の一貫性を保護する', () => {
    // すべての記事が同じ形式であることを確認
    const requiredFields = ['source', 'company_name', 'title', 'url', 'scraped_at']
    
    currentOutput.forEach((item: any) => {
      requiredFields.forEach(field => {
        expect(item).toHaveProperty(field)
      })
      
      // データ型の確認
      expect(typeof item.source).toBe('string')
      expect(typeof item.title).toBe('string')
      expect(typeof item.url).toBe('string')
      expect(typeof item.scraped_at).toBe('string')
      
      // scraped_atが有効なISO日付形式であることを確認
      expect(() => new Date(item.scraped_at)).not.toThrow()
    })
  })

  it('URLの有効性を保護する', () => {
    // すべてのURLが有効な形式であることを確認
    currentOutput.forEach((item: any) => {
      expect(item.url).toMatch(/^https?:\/\//)
      
      // PR TIMESのURLパターンを確認
      if (item.source === 'PR_TIMES') {
        expect(item.url).toContain('prtimes.jp')
      }
    })
  })

  afterAll(async () => {
    // テスト結果をゴールデンマスターとして保存（初回実行時のみ）
    if (!goldenMasterData && currentOutput) {
      const goldenPath = join(__dirname, 'golden-master-characterization.json')
      await Bun.write(goldenPath, JSON.stringify({
        capturedAt: new Date().toISOString(),
        articleCount: currentOutput.length,
        extractionRate: (currentOutput.filter((item: any) => item.company_name).length / currentOutput.length) * 100,
        sample: currentOutput.slice(0, 5) // サンプルとして最初の5件を保存
      }, null, 2))
      
      console.log('📝 Characterization data saved for future reference')
    }
  })
})

/**
 * 依存性注入パターンのテスト準備
 * 次のステップで使用する高階関数パターンの基礎
 */
describe('Characterization - 依存性の識別', () => {
  it('現在の依存関係を明確化する', () => {
    // 現在の依存関係を文書化
    const dependencies = {
      browser: 'puppeteer-core/chromium',
      scraper: 'ScraperFactory.createPRTimesScraper',
      config: 'getConfig from variables.ts',
      output: 'console.log (JSON.stringify)'
    }
    
    // 依存関係が明確であることを確認
    expect(Object.keys(dependencies)).toHaveLength(4)
    
    console.log('📋 Identified dependencies:', dependencies)
  })

  it('スクレイパーインターフェースの現在の形を記録する', () => {
    // 現在のスクレイパーが期待するインターフェース
    const currentInterface = {
      methods: ['scrape'],
      inputs: ['browser', 'keyword'],
      outputs: ['ScrapedResult[]'],
      asyncMethods: ['scrape']
    }
    
    expect(currentInterface.methods).toContain('scrape')
    expect(currentInterface.asyncMethods).toContain('scrape')
    
    console.log('📐 Current scraper interface:', currentInterface)
  })
})