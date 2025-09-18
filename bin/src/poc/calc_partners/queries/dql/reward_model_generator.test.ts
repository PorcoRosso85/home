/**
 * Reward Model Generator Test
 * 
 * 経営者の痛み: 「3日間悩んでも最適な報酬モデルが決められない」
 * 解決: 業界標準に基づく3つの明確な選択肢を即座に提示
 */

import { test } from 'node:test'
import assert from 'node:assert'
import { setupTestDatabase, loadQuery } from './test-helper.ts'

test('報酬モデル・ジェネレーター - CEOの3日間の悩みを3分で解決', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // CEOが答えられる3つの質問だけ
    const monthlyPrice = 20000      // 「うちの月額は2万円」
    const avgContractMonths = 24    // 「平均2年は使ってもらえる」 
    const maxCPA = 160000          // 「16万円までなら獲得コストOK」
    
    // クエリ実行
    const query = loadQuery('./reward_model_generator.cypher')
    const queryWithParams = query
      .replace(/\$monthlyPrice/g, monthlyPrice.toString())
      .replace(/\$avgContractMonths/g, avgContractMonths.toString())
      .replace(/\$maxCPA/g, maxCPA.toString())
    
    const result = await conn.query(queryWithParams)
    const models = await result.getAllObjects()
    
    console.log('\n🎯 3つの報酬モデルを即座に提示:')
    models.forEach(m => {
      console.log(`\n【${m.プラン名}】`)
      console.log(`  報酬率: ${m.報酬率}%`)
      console.log(`  業界事例: ${m.業界ベンチマーク}`)
      console.log(`  選ぶ理由: ${m.選択理由}`)
      console.log(`  利益率: ${m.利益率}%`)
      console.log(`  CPA判定: ${m.CPA判定}`)
    })
    
    // 検証: 必ず3つの選択肢が提示される
    assert.strictEqual(models.length, 3, '3つの明確な選択肢を提示')
    
    // 検証: Conservative < Balanced < Aggressive の順
    assert.strictEqual(models[0].報酬率, 10, 'Conservative: 10%')
    assert.strictEqual(models[1].報酬率, 20, 'Balanced: 20%')
    assert.strictEqual(models[2].報酬率, 30, 'Aggressive: 30%')
    
    // 検証: 各モデルに業界ベンチマークがある
    models.forEach(model => {
      assert(model.業界ベンチマーク, `${model.プラン名}に業界事例がある`)
      assert(model.選択理由, `${model.プラン名}に選択理由がある`)
    })
    
    // 検証: CPA判定が機能している
    const ltv = monthlyPrice * avgContractMonths // 480,000円
    models.forEach(model => {
      const reward = ltv * (model.報酬率 / 100)
      if (reward <= maxCPA) {
        assert.strictEqual(model.CPA判定, '✅ CPA内', 
          `${model.プラン名}: 報酬${reward}円はCPA内`)
      } else {
        assert.strictEqual(model.CPA判定, '⚠️ CPA超過',
          `${model.プラン名}: 報酬${reward}円はCPA超過`)
      }
    })
    
    console.log('\n✅ CEOの声: 「3日悩んだ答えが3分で出た！」')
    
    await result.close()
  } finally {
    await close()
  }
})

test('CPA超過シナリオでも適切な警告', async () => {
  const { conn, close } = await setupTestDatabase()
  
  try {
    // CPAが厳しいケース
    const monthlyPrice = 10000      // 月額1万円
    const avgContractMonths = 12    // 1年継続
    const maxCPA = 20000           // CPA2万円（LTVの16.7%のみ）
    
    const query = loadQuery('./reward_model_generator.cypher')
    const queryWithParams = query
      .replace(/\$monthlyPrice/g, monthlyPrice.toString())
      .replace(/\$avgContractMonths/g, avgContractMonths.toString())
      .replace(/\$maxCPA/g, maxCPA.toString())
    
    const result = await conn.query(queryWithParams)
    const models = await result.getAllObjects()
    
    // Aggressive（30%）はCPA超過のはず
    const aggressive = models.find(m => m.プラン名.includes('Aggressive'))
    assert.strictEqual(aggressive.CPA判定, '⚠️ CPA超過',
      'CPAを超える場合は警告を表示')
    
    // でも選択肢として表示はされる（CEOが判断できるように）
    assert.strictEqual(models.length, 3, 
      'CPA超過でも3つの選択肢は必ず表示')
    
    console.log('✅ CPA超過でも選択肢を提示（CEOが最終判断）')
    
    await result.close()
  } finally {
    await close()
  }
})