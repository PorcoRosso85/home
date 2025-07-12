# Requirement Template System (RTS)

継続的なフィードバックループを通じて、整合性が高く重複の少ない要件グラフを構築するシステム。

## なぜRTSか

- **要件の重複・矛盾を防ぐ**: 類似検索により既存要件との関係を明確化
- **テンプレートベースで安全な操作**: 検証されたパラメータのみ受付
- **類似検索による知的支援**: VSS/FTSハイブリッド検索で関連要件を発見

## 本質

概念とその関係性を有向グラフとして管理する汎用システム。適用領域は使用者が定義する。

## アーキテクチャ

- [`domain/`](./domain/README.md) - 要件グラフのルールと制約
- [`application/`](./application/README.md) - 操作可能なユースケース  
- [`infrastructure/`](./infrastructure/README.md) - 技術的実現手段

## クイックスタート

```bash
# 開発環境
nix develop

# 初期化
nix run .#init

# 実行
echo '{"type": "template", "template": "create_requirement", "parameters": {...}}' | nix run .#run
```

詳細な使用例は `mod.py` を参照。

## システムの本質

要件グラフを不整合なくなるようフィードバックすることで、適切な入力を受け付けてグラフビルドしていく。この本質は[requirement/graph](../graph/README.md)から一切変わっていない。