# KuzuDB WASM リアルタイム同期システム

ブラウザ間でKuzuDB WASMインスタンスをリアルタイム同期するシステムの設計・実装ドキュメントです。

## 概要

Matthew Weidner氏の「Collaborative Text Editing without CRDTs or OT」のアプローチを採用し、最小限のサーバー機能で安全かつ効率的な同期を実現します。

## ドキュメント構成

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