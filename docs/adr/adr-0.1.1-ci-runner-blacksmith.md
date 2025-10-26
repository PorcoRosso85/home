# ADR 0.1.1: CI実行基盤の標準化（Blacksmith）

- **Status**: Accepted
- **Date**: 2025-10-26 (JST)
- **Relates**: ADR 0.1.0（CIガード/参照規約）

## 1. 目的

- CIは Blacksmith のマネージド self-hosted runner を **標準** とする。
- 自前常駐 runner や GitHub ホスト runner は原則不採用（必要時は「例外」を明記）。

## 2. 採用理由（要約）

- **性能**: ベアメタル級CPU／近接キャッシュ／（必要に応じて）Sticky Disk により高速化。
- **コスト**: 実行時間短縮＋分単価抑制により総コストを削減。
- **運用**: ランナーのライフサイクル管理不要。ジョブ単位隔離。可観測性あり。

## 3. 運用ルール

- `runs-on: blacksmith-<plan>` を標準（例: `blacksmith-2vcpu-ubuntu-2404`）。
- **キャッシュ方針**:
  - 依存キャッシュ（actions/cache）は通常利用。
  - Docker ビルドは Sticky Disk を **ビルド系ジョブに限定** して採用可（費用監視前提）。
- **例外**:
  - 特権やネットワーク要件等で Blacksmith 不可のジョブは例外 runner を許可。
  - 例外を使う場合は PR 説明に **対象ジョブ名／理由／代替 runner** を明記し、期限を設ける。

## 4. CIゲート（ADR 0.1.0との接続）

- ADR 0.1.0で定義した必須検査を **Blacksmith 上で** 実行:
  1) `nix flake lock --check` / `nix flake check`
  2) entrypath 検証（`specification/**` 直下に `flake.nix`）
  3) `inputs.*.url` の `path:` 禁止
  4) lock-only 原則（`flake.lock` 以外の差分があれば fail）
- `main` へのマージは **Blacksmith CI 緑を必須**。

## 5. 維持

- SLO/費用/キャッシュ方針の変更は本ADRを更新して通知（0.1.0は不改変）。
- Sticky Disk 等のオプションは月次で費用レビューし、対象ジョブを見直す。

## 6. 非スコープ

- Actions YAML の `runs-on` 変更、専用アクション導入、保護ブランチ設定は **別PR**。
