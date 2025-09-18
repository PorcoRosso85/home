# Claude Graph POC - KuzuDBによる自律的タスク探索・計画

## 概要
このPOCは、ClaudeがKuzuDB内のグラフ構造を参照することで、自律的にタスクを探索し、計画を立てる能力を実証します。

## 目的
- KuzuDBに格納された要件・コード・テスト情報をClaudeが自ら探索
- グラフ構造を理解してタスクの依存関係を把握
- 自動的に作業計画を生成し、実行順序を決定

## アーキテクチャ

```
┌─────────────────────┐
│     Claude AI       │
│  (Task Planner)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Graph Explorer    │
│   (TypeScript)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      KuzuDB         │
│  (Graph Database)   │
└─────────────────────┘
```

## 主要コンポーネント

### 1. Task Explorer (`taskExplorer.ts`)
- KuzuDBのグラフを探索し、タスク関連情報を取得
- 要件、実装、テストの関係性を解析

### 2. Task Planner (`taskPlanner.ts`)
- 探索結果を基にタスク計画を生成
- 依存関係を考慮した実行順序の決定

### 3. Claude Integration (`claudeIntegration.ts`)
- Claudeがグラフ情報を理解しやすい形式に変換
- 自然言語での計画説明を生成

### 4. Query Templates (`queries/`)
- タスク探索用のCypherクエリテンプレート
- 要件トレーサビリティクエリ

## 使用例

```typescript
// Claudeが自律的にタスクを探索・計画
const planner = new ClaudeTaskPlanner(kuzuConnection);

// 要件IDからタスク計画を生成
const plan = await planner.planTasksForRequirement("req_user_auth");

// 実装が必要なコードエンティティを探索
const unimplementedTasks = await planner.findUnimplementedRequirements();

// テストが不足している要件を発見
const untested = await planner.findUntestedRequirements();
```

## KuzuDBスキーマ活用

このPOCは既存のKuzuDBスキーマを活用：
- `RequirementEntity`: タスクの源となる要件
- `CodeEntity`: 実装タスク
- `IS_IMPLEMENTED_BY`: 要件と実装の関係
- `IS_VERIFIED_BY`: 要件とテストの関係
- `DEPENDS_ON`: タスク間の依存関係

## 期待される成果
1. Claudeが要件グラフを読み取り、自動的に作業順序を決定
2. 実装・テストの不足を発見し、タスクリストを生成
3. 依存関係を考慮した最適な実行計画の提案