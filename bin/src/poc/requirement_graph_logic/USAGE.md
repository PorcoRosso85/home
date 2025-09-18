# RGL - 開発決定事項管理ツール

## 概要

RGL (Requirement Graph Logic) を使って開発中の決定事項を管理します。決定の重複を防ぎ、過去の決定との関連性を発見し、決定の品質を向上させます。

## インストール

```bash
# 実行権限を付与（初回のみ）
chmod +x /home/nixos/bin/src/rgl

# パスに追加またはエイリアス設定
alias rgl="/home/nixos/bin/src/rgl"
```

## 基本的な使い方

### 新しい決定事項を追加

```bash
# シンプルな追加
rgl add "認証機能にJWTを使用することに決定"

# タイプとタグを指定
rgl add "DBをKuzuDBに移行" --type decision --tags database,architecture

# タイプの種類: decision, problem, solution, todo
```

### 決定事項を表示

```bash
# 最近の10件を表示（デフォルト）
rgl list

# 件数を指定
rgl list -n 20
```

### 検索

```bash
# キーワードで検索
rgl search "認証"

# 類似の決定事項を発見
rgl search "JWT" -n 10
```

### 統計情報

```bash
# 全体の統計を表示
rgl stats
```

## 実際の使用例

### 1. 開発開始時

```bash
$ rgl add "プロジェクトの目的: 要件管理システムの構築" --type decision --tags project
✅ 決定事項を追加しました
   ID: REQ-xxx

📊 品質スコア:
   独自性: 1.00  # 最初なので完全に独自
   明確性: 0.90  # 明確な記述
   完全性: 0.66  # やや詳細が不足
```

### 2. 技術選定

```bash
$ rgl add "フロントエンドにReactを採用" --type decision --tags frontend,tech-stack
✅ 決定事項を追加しました

$ rgl add "フロントエンドにVueを採用" --type decision --tags frontend,tech-stack
⚠️ 類似の決定事項:
   - フロントエンドにReactを採用 (類似度: 0.85)
   
💡 改善提案:
   - 既存の決定と矛盾する可能性があります
```

### 3. 問題と解決策の記録

```bash
# 問題を記録
$ rgl add "本番環境でメモリリークが発生" --type problem --tags bug,production

# 解決策を記録
$ rgl add "メモリリーク: イベントリスナーの解放漏れが原因。useEffectのクリーンアップを追加" --type solution --tags bug,production
```

### 4. 決定の変遷を追跡

```bash
$ rgl list -n 20
📋 最近の決定事項（20件）:

[1] v3.0.0: requirement_typeを細分化
[2] v2.1.0: 決済機能を追加
[3] v2.0.1: 認証にJWTを使用（詳細化）
[4] v2.0.0: 認証機能を実装（初期決定）
```

## 高度な使い方

### 環境変数

```bash
# 決定事項ファイルの場所を変更
export RGL_FILE=/path/to/custom/decisions.jsonl
rgl add "カスタム場所に保存"
```

### KuzuDBとの統合（将来）

決定事項はKuzuDBのVersionStateとして保存可能：

```cypher
// RGLの決定をKuzuDBに記録
CREATE (d:Decision {
    id: "REQ-xxx",
    text: "認証にJWTを使用",
    version: "v2.0.1",
    scores: {uniqueness: 0.8, clarity: 0.9}
})
```

## データ形式

決定事項は `~/.rgl/decisions.jsonl` に保存されます：

```json
{"id": "REQ-xxx", "text": "決定内容", "embedding": {...}, "metadata": {...}}
```

## ベストプラクティス

1. **具体的に記述**: 「認証」ではなく「認証にJWTを使用」
2. **タグを活用**: 後で検索しやすくなる
3. **タイプを使い分け**: decision/problem/solution/todo
4. **定期的に確認**: `rgl stats`で傾向を把握

## トラブルシューティング

### "command not found"

```bash
# フルパスで実行
/home/nixos/bin/src/rgl add "テスト"

# またはPythonモジュールとして
python -m poc.requirement_graph_logic add "テスト"
```

### 類似度が低すぎる/高すぎる

現在は簡易的な埋め込みを使用。将来的にsentence-transformersに移行予定。