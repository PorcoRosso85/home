# Requirement Graph Logic (RGL)

階層化された要件を管理し、整合性の摩擦を可視化するシステム。

## ビジョン

組織の各階層（経営層、プロダクトマネージャー、エンジニア）が同じ要件データベースに対して独立して要件を追加・更新する中で、発生する摩擦や不整合を自動的に検出し、プロジェクトの健全性を定量的に示す。

## システムの流れ

```
┌─────────┐        ┌──────────┐        ┌─────────┐
│ Me/LLM  │        │  System  │        │ KuzuDB  │
└────┬────┘        └────┬─────┘        └────┬────┘
     │                   │                   │
     │ Cypher Query      │                   │
     ├──────────────────>│                   │
     │                   │                   │
     │                   ├─ 1. 階層検証    │
     │                   │  (事前チェック)  │
     │                   │                   │
     │                   │  NG: score -1.0  │
     │<───────────────────┤  即座にエラー返却│
     │                   │                   │
     │                   │  OK: 次へ進む    │
     │                   ├─ 2. クエリ実行   │
     │                   ├──────────────────>│
     │                   │                   │
     │                   │ Result            │
     │                   │<──────────────────│
     │                   │                   │
     │                   ├─ 3. 摩擦分析     │
     │                   │  (CREATE時のみ)  │
     │                   │                   │
     │ JSONL Response    │                   │
     │<──────────────────┤                   │
     │ (result + score)  │                   │
     │                   │                   │
```

### 低スコアが返される例

```
Me/LLM: タスク「UI実装」を作成し、ビジョン「システム全体構想」に依存させる
System: {"type": "error", "score": -1.0, "message": "階層違反: タスク(Level 4)がビジョン(Level 0)に直接依存"}

Me/LLM: 同じ要件IDで「ユーザビリティ向上」と「パフォーマンス最適化」を作成
System: {"type": "error", "score": -1.0, "message": "自己参照: 同一ノードへの依存"}

Me/LLM: A→B→C→Aという依存関係を作成
System: {"type": "error", "score": -1.0, "message": "循環参照: 依存関係に循環を検出"}

Me/LLM: 「使いやすいUI」という曖昧な要件を追加
System: {"type": "score", "data": {"frictions": {"ambiguity": -0.6}, "total": {"total_score": -0.12, "health": "healthy"}}}

Me/LLM: 複数のチームが同じ機能に対して異なる優先度で要件を追加
System: {"type": "score", "data": {"frictions": {"priority": -0.7}, "total": {"total_score": -0.21, "health": "needs_attention"}}}
```

このフィードバックにより、要件を修正して再投入することで、最終的に整合性のとれた要件グラフが構築されます。

## クイックスタート

```bash
# 開発環境の起動
nix develop

# テストの実行
nix run .#test

# アプリケーションの実行
nix run
```

## 使い方

```bash
echo '{"type": "cypher", "query": "CREATE ..."}' | \
  LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/ \
  RGL_DB_PATH=./rgl_db \
  python run.py
```

## 出力フォーマット

すべての出力は JSONL (JSON Lines) 形式で標準出力に返されます。

```jsonl
{"type": "log", "level": "info", "timestamp": "2025-01-03T12:34:56Z", "module": "main", "message": "Processing query"}
{"type": "result", "level": "info", "timestamp": "2025-01-03T12:34:57Z", "data": [...]}
{"type": "score", "level": "warn", "timestamp": "2025-01-03T12:34:58Z", "data": {"frictions": {...}, "total": {"total_score": -0.5, "health": "needs_attention"}}}
{"type": "error", "level": "error", "timestamp": "2025-01-03T12:34:59Z", "message": "Hierarchy violation detected", "score": -1.0}
```