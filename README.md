# UGC × PSEO Platform

## 概要
UGC（ユーザー生成コンテンツ）とPSEO（プログラマティックSEO）を組み合わせたプラットフォーム

## ディレクトリ構造
- `features/`: 機能提供層（dee）
- `deployables/`: デプロイ可能な実アプリ/バッチ（der）
- `policy/`: 契約検証ポリシーとgateツール
- `flakes/contracts-index/`: index自動生成flake
- `docs/`: ADRと規約
- `platform/`: 共通基盤
- `env/`, `secrets/`: 環境変数と機密情報
- `ci/`: CI成果物とレポート

## CI最小UX
1. `nix build .#contracts-index`
2. `nix run .#gate -- lint --all`
3. `nix run .#gate -- lint contracts`
4. `nix run .#gate -- plan --changed-only`
5. `nix run .#gate -- smoke`

詳細は `docs/adr/0.10.5-rc3.md` を参照
