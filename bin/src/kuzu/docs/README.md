# KuzuDB Documentation

このディレクトリには、KuzuDBを使用したシステムに関するドキュメントが含まれています。

## ドキュメント一覧

### DAG管理システム（2024-06-18追加）

1. **[kuzu_dag_overview.md](kuzu_dag_overview.md)**
   - KuzuDBによる未来志向DAG管理システムの概要
   - Version-URIを中心とした設計思想
   - Bauplanとの違いと基本的なスキーマ設計

2. **[kuzu_dag_validation.md](kuzu_dag_validation.md)**
   - 論理的整合性の検証方法
   - 事前検証と事後検証の実装例
   - 決済機能開発の実例を通じた検証

3. **[kuzu_dag_llm_architecture.md](kuzu_dag_llm_architecture.md)**
   - LLM時代の意図駆動型アーキテクチャ記述言語
   - 厳密さを捨てて継続性を重視する設計
   - 人間とLLMの協働を前提とした最小構成

4. **[kuzu_dag_practical_guide.md](kuzu_dag_practical_guide.md)**
   - 実証済みの動作例とテストケース
   - KuzuDBの制限事項と回避方法
   - すぐに使えるクエリテンプレート

### WASM リアルタイム同期システム

Matthew Weidner氏の「Collaborative Text Editing without CRDTs or OT」のアプローチを採用し、最小限のサーバー機能で安全かつ効率的な同期を実現します。

- [concept.md](./concept.md) - 設計思想とコアコンセプト
- [protocol.md](./protocol.md) - 同期プロトコル仕様
- [implementation.md](./implementation.md) - 実装ガイド

## 主な特徴

1. **サーバーバージョン管理** - クライアントタイムスタンプ（LWW）ではなく、サーバーが操作順序を決定
2. **プロパティレベル操作** - `set_property`/`remove_property`による細粒度の更新
3. **パラメータ化クエリ** - Cypherインジェクション対策を必須化
4. **最小構成** - DO + R2 + WebSocketで実現

## クイックスタート

```bash
# サーバー起動
cd sync
deno run --allow-net server.ts

# ブラウザでindex.htmlを開く（2つのウィンドウ）
# ノード作成して同期を確認
```

## セキュリティ

- クエリの直接送信は禁止
- パッチ（操作の意図）のみを送信
- 各クライアントでパラメータ化クエリを使用してローカル実行

## 今後の拡張

- エッジ操作の追加
- 競合解決の高度化
- 認証・権限管理
- パフォーマンス最適化