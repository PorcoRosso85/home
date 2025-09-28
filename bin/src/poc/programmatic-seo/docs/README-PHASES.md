DELETE AFTER FULL COMPLETION OF PHASE 1.x

概要
- このリポは Phase1 を 1.0 → 1.7 に分割し、各フェーズごとに実装と検収を進める。
- 各フェーズには専用の指示書がある。必ず実装前に熟読し、完了後は指示書ファイルを削除すること。
- rwsdk-init は「壊れないSSR/Assets/Routingの最小リファレンス」。Phase1のUIはここを起点に進めるが、エッジ基盤は別Workerで分離する。

運用原則（5原則）
- SRP/KISS: UI(SSR) と基盤(計測/サイトマップ/ISR) は別Worker。各Workerは単機能で小さく。
- DRY: 共通処理は packages/ に集約。各Workerは薄く呼び出すだけ。
- YAGNI: 1.2 まではP0最小セットのみ。Queues/R2/i18n/RateLimit/Observabilityは以降で段階導入。
- SOLID: ストレージや外部依存はインターフェース越しに注入。HTTP契約を安定させる。

命名・構成ルール
- UI: interfaces/site（rwsdk-init を移設/統合）。
- 最小エッジ: interfaces/edge-min（/ingest, /r/:id, /sitemap*, /revalidate）。
- 分割後: interfaces/{tracker,sitemap,edge-cache}。
- 共有束縛: infra-config/cloudflare/wrangler.shared.toml を作り、各 wrangler.toml から extends。
- D1マイグレーション: infra-config/cloudflare/d1.migrations/ に時系列で .sql を追加。

rwsdk-init の扱い
- 変更しない（常にデプロイ成功状態を維持）。
- programmatic-seo 側 flake の inputs で参照して devShell/ツールチェーンと SSR 実機検証環境として活用。

進め方（推奨）
1) 1.0 → 1.1（ゼロCFで土台）
2) 1.2（最小Edgeを導入＋rwsdk-init統合）
3) 1.3 以降で分割/分析/多言語/同意/可観測性を段階導入

検収観点（共通）
- ビルド/デプロイ: UI と Edge は独立に成功し、どちらかの失敗が他方に波及しない。
- インデックス制御: draft/noindex → index の昇格がルール化されている（1.3+）。
- キャッシュ: Cache-Control と SWR が意図通り。/revalidate が動く（1.2+）。
- セキュリティ: 必要最小の権限のみを Worker に付与。
