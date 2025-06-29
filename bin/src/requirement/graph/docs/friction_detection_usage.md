# リアルタイム摩擦検出機能の使い方

## 概要

要件管理システムは、要件を作成するたびに自動的に「摩擦」を検出し、プロジェクトの健全性についてリアルタイムでフィードバックを提供します。

## 動作の仕組み

### 1. 要件作成時の自動検出

CREATEクエリでRequirementEntityを作成すると、システムは自動的に以下を実行：

1. 既存の要件データを分析
2. 4種類の摩擦を検出
3. 総合スコアを計算
4. 必要に応じてアラートを生成

### 2. レスポンスの構造

```json
{
  "status": "success",
  "data": [...],
  "friction_analysis": {
    "frictions": {
      "ambiguity": {"score": -0.6, "message": "要件に複数の解釈が存在します"},
      "priority": {"score": -0.4, "message": "critical要件が複数存在します"},
      "temporal": {"score": 0.0, "message": "要件は安定しています"},
      "contradiction": {"score": -0.4, "message": "矛盾する要求があります"}
    },
    "total": {
      "total_score": -0.45,
      "health": "needs_attention",
      "recommendation": "週次レビューでの確認を推奨"
    }
  },
  "alert": {
    "level": "warning",
    "message": "プロジェクトの健全性: needs_attention",
    "recommendation": "週次レビューでの確認を推奨",
    "score": -0.45
  }
}
```

## 摩擦の種類

### 1. 曖昧性摩擦
- 検出方法: タイトルに曖昧な単語（「フレンドリー」「使いやすい」等）
- 影響: 開発者間で解釈の相違が生じる

### 2. 優先度摩擦
- 検出方法: priority = 'critical'の要件数
- 影響: リソース競合、スケジュール遅延

### 3. 時間経過摩擦
- 検出方法: バージョン履歴の分析
- 影響: 要件の変質、スコープクリープ

### 4. 矛盾摩擦
- 検出方法: 相反する目標（コスト削減 vs 性能向上）
- 影響: 実装の困難、意思決定の停滞

## アラートレベル

| 総合スコア | 健全性 | 対応 |
|-----------|--------|------|
| > -0.2 | healthy | 継続的なモニタリング |
| -0.2 〜 -0.5 | needs_attention | 週次レビューで確認 |
| -0.5 〜 -0.7 | at_risk | 即座の介入が必要 |
| < -0.7 | critical | プロジェクトの根本的見直し |

## 使用例

### 例1: 曖昧な要件でアラート

```cypher
CREATE (r:RequirementEntity {
    id: 'req_001',
    title: 'ユーザーフレンドリーな画面設計',
    priority: 'high'
})
```

→ 曖昧性摩擦 -0.6 のアラート

### 例2: 複数のcritical要件

```cypher
CREATE (r:RequirementEntity {
    id: 'req_003',
    title: '新機能開発',
    priority: 'critical'
})
```

→ 3つ目のcritical要件で優先度摩擦のアラート

### 例3: 明確な要件（アラートなし）

```cypher
CREATE (r:RequirementEntity {
    id: 'req_004',
    title: 'ユーザー認証API実装',
    description: 'JWT認証を使用したREST API',
    priority: 'medium',
    technical_specifications: '{"auth": "JWT", "framework": "FastAPI"}'
})
```

→ 摩擦なし、健全な要件

## 摩擦への対処法

### 曖昧性摩擦への対処
1. 要件の具体化ワークショップを実施
2. 受け入れ基準を明確に定義
3. 技術仕様を詳細化

### 優先度摩擦への対処
1. ステークホルダー会議で優先順位を調整
2. リソース配分の見直し
3. フェーズ分けによる段階的実装

### 時間経過摩擦への対処
1. 要件の定期レビュー
2. 変更管理プロセスの強化
3. スコープの再定義

### 矛盾摩擦への対処
1. トレードオフ分析
2. 代替案の検討
3. ステークホルダー間の合意形成

## 設定とカスタマイズ

摩擦検出の閾値やルールは以下で管理：
- スコア定義: `application/scoring_service.py`
- 検出ロジック: `application/friction_detector.py`
- 詳細仕様: `docs/friction_scoring_specification.md`