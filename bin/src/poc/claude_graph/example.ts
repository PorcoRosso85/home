/**
 * Claude Graph POC - 使用例
 * ClaudeがKuzuDBを使って自律的にタスクを探索・計画する例
 */

import { Database } from 'kuzu';
import { ClaudeTaskPlanner } from './claudeIntegration.ts';

// データベース接続の例
async function connectToKuzu(): Promise<Database> {
  // 実際の接続設定に置き換えてください
  const db = new Database('./kuzu_db');
  await db.init();
  return db;
}

async function main() {
  console.log('Claude Graph POC - タスク自律探索・計画デモ\n');
  
  const db = await connectToKuzu();
  const claudePlanner = new ClaudeTaskPlanner(db);

  // 例1: 自然言語でタスクを理解して計画
  console.log('=== 例1: 自然言語リクエストの処理 ===');
  const request1 = "req_user_auth の実装とテストを計画してください";
  const result1 = await claudePlanner.understandAndPlan(request1);
  
  console.log('解釈:', result1.interpretation);
  console.log('\n生成された計画:');
  result1.plans.forEach(plan => {
    console.log(`- ${plan.id}`);
    console.log(`  タスク数: ${plan.tasks.length}`);
    console.log(`  推定時間: ${plan.totalEstimatedTime}分`);
    console.log(`  説明:\n${plan.explanation}`);
  });

  console.log('\nインサイト:');
  result1.insights.forEach(insight => {
    console.log(`- [${insight.type}] ${insight.message}`);
    console.log(`  推奨アクション: ${insight.suggestedActions.join(', ')}`);
  });

  // 例2: 現在の状態を説明
  console.log('\n=== 例2: プロジェクト状態の説明 ===');
  const stateExplanation = await claudePlanner.explainCurrentState();
  console.log(stateExplanation);

  // 例3: 次のアクション提案
  console.log('\n=== 例3: 次のアクション提案 ===');
  const suggestions = await claudePlanner.suggestNextActions();
  suggestions.forEach(suggestion => {
    console.log(`\n[${suggestion.type}] ${suggestion.message}`);
    console.log('関連エンティティ:', suggestion.relatedEntities.join(', '));
    console.log('推奨アクション:');
    suggestion.suggestedActions.forEach(action => {
      console.log(`  - ${action}`);
    });
  });

  // 例4: キーワードベースの探索
  console.log('\n=== 例4: キーワードベースの探索 ===');
  const request2 = "認証とセキュリティに関する要件を探して実装計画を作成";
  const result2 = await claudePlanner.understandAndPlan(request2);
  
  console.log('解釈:', result2.interpretation);
  console.log('見つかった関連要件数:', result2.insights.filter(i => i.type === 'info').length);

  // 例5: タスク完了の記録
  console.log('\n=== 例5: タスク進捗の追跡 ===');
  if (result1.plans.length > 0 && result1.plans[0].tasks.length > 0) {
    const firstTask = result1.plans[0].tasks[0];
    console.log(`タスク "${firstTask.title}" を完了としてマーク`);
    claudePlanner.markTaskCompleted(firstTask.id);
    
    // 更新後の状態を確認
    const updatedState = await claudePlanner.explainCurrentState();
    console.log('\n更新後の状態:');
    console.log(updatedState);
  }

  // 例6: 複雑な依存関係の計画
  console.log('\n=== 例6: 依存関係を考慮した計画 ===');
  const request3 = "req_payment_processing を実装したいが、依存関係も含めて計画して";
  const result3 = await claudePlanner.understandAndPlan(request3);
  
  if (result3.plans.length > 0) {
    const plan = result3.plans[0];
    console.log('依存関係グラフ:');
    console.log(`  ノード数: ${plan.dependencies.nodes.length}`);
    console.log(`  エッジ数: ${plan.dependencies.edges.length}`);
    
    console.log('\nタスク実行順序:');
    plan.tasks.forEach((task, index) => {
      console.log(`  ${index + 1}. ${task.title}`);
      if (task.prerequisites.length > 0) {
        console.log(`     前提: ${task.prerequisites.join(', ')}`);
      }
    });
  }

  await db.close();
}

// 実行
main().catch(console.error);