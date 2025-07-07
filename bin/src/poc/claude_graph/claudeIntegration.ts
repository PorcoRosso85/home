/**
 * Claude Integration - Claudeがグラフ情報を理解し活用するための統合モジュール
 */

import { TaskPlanner, type TaskPlan } from './taskPlanner.ts';
import { TaskExplorer, type ExplorationResult } from './taskExplorer.ts';
import type { Database } from 'kuzu';

interface ClaudeContext {
  currentRequirement?: string;
  explorationHistory: ExplorationResult[];
  activePlans: TaskPlan[];
  completedTasks: string[];
}

interface ClaudeInsight {
  type: 'recommendation' | 'warning' | 'info';
  message: string;
  relatedEntities: string[];
  suggestedActions: string[];
}

class ClaudeTaskPlanner {
  private planner: TaskPlanner;
  private explorer: TaskExplorer;
  private context: ClaudeContext;

  constructor(private db: Database) {
    this.planner = new TaskPlanner(db);
    this.explorer = new TaskExplorer(db);
    this.context = {
      explorationHistory: [],
      activePlans: [],
      completedTasks: []
    };
  }

  /**
   * Claudeが自然言語でタスクを理解し、計画を生成
   */
  async understandAndPlan(naturalLanguageRequest: string): Promise<{
    interpretation: string;
    plans: TaskPlan[];
    insights: ClaudeInsight[];
  }> {
    // 自然言語から要件IDやキーワードを抽出（簡易実装）
    const requirementIds = this.extractRequirementIds(naturalLanguageRequest);
    const keywords = this.extractKeywords(naturalLanguageRequest);

    const plans: TaskPlan[] = [];
    const insights: ClaudeInsight[] = [];

    // 要件IDが明示されている場合
    if (requirementIds.length > 0) {
      for (const reqId of requirementIds) {
        const plan = await this.planner.planTasksForRequirement(reqId);
        plans.push(plan);
        
        // 探索結果を記録
        const exploration = await this.explorer.exploreFromRequirement(reqId);
        this.context.explorationHistory.push(exploration);
        
        // インサイトを生成
        insights.push(...this.generateInsights(exploration, plan));
      }
    }

    // キーワードベースの探索
    if (keywords.length > 0) {
      const relevantRequirements = await this.searchRequirementsByKeywords(keywords);
      insights.push({
        type: 'info',
        message: `キーワード "${keywords.join(', ')}" に関連する要件が ${relevantRequirements.length} 件見つかりました`,
        relatedEntities: relevantRequirements.map(r => r.id),
        suggestedActions: relevantRequirements.slice(0, 3).map(r => 
          `要件 ${r.id} (${r.title}) の実装計画を作成`
        )
      });
    }

    return {
      interpretation: this.interpretRequest(naturalLanguageRequest, requirementIds, keywords),
      plans,
      insights
    };
  }

  /**
   * 現在のコンテキストから次のアクションを提案
   */
  async suggestNextActions(): Promise<ClaudeInsight[]> {
    const insights: ClaudeInsight[] = [];

    // 未実装要件のチェック
    const unimplemented = await this.explorer.findUnimplementedRequirements();
    if (unimplemented.length > 0) {
      insights.push({
        type: 'recommendation',
        message: `${unimplemented.length}件の未実装要件があります`,
        relatedEntities: unimplemented.slice(0, 5).map(r => r.id),
        suggestedActions: [
          '高優先度の要件から実装開始',
          'バッチ実装計画の作成',
          '依存関係の確認'
        ]
      });
    }

    // テスト不足のチェック
    const untested = await this.explorer.findUntestedRequirements();
    if (untested.length > 0) {
      insights.push({
        type: 'warning',
        message: `${untested.length}件の要件にテストがありません`,
        relatedEntities: untested.slice(0, 5).map(r => r.id),
        suggestedActions: [
          'テストカバレッジの向上',
          'critical要件のテスト優先実施'
        ]
      });
    }

    return insights;
  }

  /**
   * タスクの進捗を追跡
   */
  markTaskCompleted(taskId: string): void {
    this.context.completedTasks.push(taskId);
    
    // 関連する計画を更新
    this.context.activePlans.forEach(plan => {
      const task = plan.tasks.find(t => t.id === taskId);
      if (task) {
        task.status = 'completed';
      }
    });
  }

  /**
   * グラフの現在状態を自然言語で説明
   */
  async explainCurrentState(): Promise<string> {
    const totalReqs = await this.countTotalRequirements();
    const implemented = await this.countImplementedRequirements();
    const tested = await this.countTestedRequirements();

    const implementationRate = (implemented / totalReqs * 100).toFixed(1);
    const testCoverage = (tested / totalReqs * 100).toFixed(1);

    const explanation = [
      '## 現在のプロジェクト状態',
      '',
      `- 総要件数: ${totalReqs}`,
      `- 実装済み: ${implemented} (${implementationRate}%)`,
      `- テスト済み: ${tested} (${testCoverage}%)`,
      '',
      '## アクティブな計画',
      ...this.context.activePlans.map(p => 
        `- ${p.id}: ${p.tasks.length}タスク (${p.tasks.filter(t => t.status === 'completed').length}完了)`
      ),
      '',
      '## 最近の探索',
      ...this.context.explorationHistory.slice(-5).map(e => 
        `- ${e.nodes.length}ノード, ${e.insights.length}インサイト`
      )
    ];

    return explanation.join('\n');
  }

  private extractRequirementIds(text: string): string[] {
    const pattern = /req_[a-zA-Z0-9_]+/g;
    return text.match(pattern) || [];
  }

  private extractKeywords(text: string): string[] {
    // 簡易的なキーワード抽出
    const stopWords = ['の', 'を', 'に', 'で', 'と', 'が', 'は'];
    return text.split(/\s+/)
      .filter(word => word.length > 2 && !stopWords.includes(word))
      .slice(0, 5);
  }

  private async searchRequirementsByKeywords(keywords: string[]): Promise<any[]> {
    const query = `
      MATCH (r:RequirementEntity)
      WHERE ${keywords.map((_, i) => `r.title CONTAINS $keyword${i} OR r.description CONTAINS $keyword${i}`).join(' OR ')}
      RETURN r.id as id, r.title as title, r.priority as priority
      LIMIT 10
    `;
    
    const params = keywords.reduce((acc, keyword, i) => {
      acc[`keyword${i}`] = keyword;
      return acc;
    }, {} as Record<string, string>);

    return await this.db.query(query, params);
  }

  private generateInsights(exploration: ExplorationResult, plan: TaskPlan): ClaudeInsight[] {
    const insights: ClaudeInsight[] = [];

    // 実装の緊急性
    if (plan.tasks.some(t => t.priority === 'high' && t.type === 'implement')) {
      insights.push({
        type: 'warning',
        message: '高優先度の実装タスクがあります',
        relatedEntities: plan.tasks.filter(t => t.priority === 'high').map(t => t.targetId),
        suggestedActions: ['即座に実装開始', '必要リソースの確認']
      });
    }

    // 依存関係の複雑さ
    if (plan.dependencies.edges.length > 5) {
      insights.push({
        type: 'info',
        message: '複雑な依存関係が検出されました',
        relatedEntities: plan.dependencies.nodes,
        suggestedActions: ['依存関係の可視化', '段階的な実装アプローチ']
      });
    }

    return insights;
  }

  private interpretRequest(request: string, requirementIds: string[], keywords: string[]): string {
    const parts = ['リクエストを理解しました。'];
    
    if (requirementIds.length > 0) {
      parts.push(`要件ID: ${requirementIds.join(', ')} に対する計画を作成します。`);
    }
    
    if (keywords.length > 0) {
      parts.push(`キーワード: ${keywords.join(', ')} で関連要件を検索します。`);
    }

    return parts.join(' ');
  }

  private async countTotalRequirements(): Promise<number> {
    const result = await this.db.query('MATCH (r:RequirementEntity) RETURN count(*) as count');
    return result[0].count;
  }

  private async countImplementedRequirements(): Promise<number> {
    const result = await this.db.query(`
      MATCH (r:RequirementEntity)
      WHERE EXISTS { MATCH (r)-[:IS_IMPLEMENTED_BY]->() }
      RETURN count(*) as count
    `);
    return result[0].count;
  }

  private async countTestedRequirements(): Promise<number> {
    const result = await this.db.query(`
      MATCH (r:RequirementEntity)
      WHERE EXISTS { MATCH (r)-[:IS_VERIFIED_BY]->() }
      RETURN count(*) as count
    `);
    return result[0].count;
  }
}

export { ClaudeTaskPlanner, type ClaudeContext, type ClaudeInsight };