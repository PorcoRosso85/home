# Repository Tree (Latest Design Only)

> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

**Last Updated**: 2025-10-23 (JST)
**対応ADR**: docs/adr/adr-0.10.12.md

---

## 最新ツリー（ADR 0.10.12 — Orchestration v4.1b）

> 凡例: ★=必須、◇=生成(非コミット推奨)、△=任意、p=フェーズ番号

```
repo/
├─ README.md                                   △  使い方/流れ
├─ docs/
│  ├─ adr/
│  │  ├─ adr-0.10.8.md                         △  SSOT-first & thin manifest
│  │  ├─ adr-0.10.10.md                        △  Flake-driven manifest
│  │  ├─ adr-0.10.11.md                        △  consumes/Secrets/SBOM/CVE
│  │  └─ adr-0.10.12.md                        ★  本ADR: Orchestration v4.1b + 構成統一リファクタ
│  ├─ tree.md                                  △  このファイル（最新構成の単一真実）
│  └─ architecture/
│     ├─ sequence-temporal.mmd                 △  WF/Signals/Timers シーケンス図
│     └─ gateway-sequence.mmd                  △  GW 起動/逆プロキシ/内部API シーケンス図
├─ contracts/
│  └─ ssot/                                    ★  契約のSSOT（人が編集）
│     ├─ _toc.yaml                             ★  契約ID↔パス索引
│     ├─ _config.cue                           ★  生成/ゲート設定
│     └─ <domain>/<subject>@<semver>/          ★  各契約
│        ├─ contract.cue                       ★  契約スキーマ/制約
│        ├─ stories/                           ★  受入シナリオ（normal/error/boundary）
│        │  ├─ normal.cue
│        │  ├─ error.cue
│        │  └─ boundary.cue
│        └─ seeds/                             △  サンプルデータ
│           └─ *.json
├─ capsules/                                   ◇  生成（非コミット）
│  └─ index.cue                                ◇  SSOT→索引（唯一の参照点）
├─ features/
│  └─ opencode-autopilot/                      ★  フラット化（余分層削除）
│     ├─ flake.nix                             ★  meta.manifest.kind="feature", contractRef...
│     ├─ application/                          ★  WF本体/ビジネスロジック
│     │  ├─ workflow.go                        ★  WF本体/SA setStage一極化
│     │  └─ manifest.cue                       ★  WF契約(SA=4,queue,timeout)
│     ├─ domain/                               ★  ドメインモデル
│     │  ├─ types.go                           ★  uri/corr-id/value objects
│     │  └─ policy.go                          ★  SLA段階/閾値
│     └─ infrastructure/                       ★  永続化/外部システム
│        └─ ssotrepo/
│           └─ libsql.go                       ★  唯一の業務DB書込口(WFのみ使用)
├─ deployables/
│  ├─ opencode-gateway/                        ★  src廃止：DDD3層直下
│  │  ├─ flake.nix                             ★  meta.manifest.kind="deployable", consumes...
│  │  ├─ manifest.cue                          ★  デプロイ契約
│  │  ├─ application/                          ★  エントリポイント/配線
│  │  │  ├─ main.go                            ★  HTTP起動(/api,/internal)
│  │  │  └─ wiring.go                          ★  DI/設定/ルータ配線
│  │  ├─ domain/                               △  ビジネスルール（必要時のみ）
│  │  │  └─ .gitkeep                           △  空層を先行確保
│  │  └─ infrastructure/                       ★  外部I/O/プロセス管理
│  │     ├─ ensure.go                          ★  ensureInstance(uri)/TTL/LRU
│  │     └─ proxy.go                           ★  /w/:wsId/* → OpenCode 逆プロキシ
│  └─ opencode-worker/                         ★  Temporal Worker
│     ├─ flake.nix                             ★
│     ├─ manifest.cue                          ★
│     ├─ application/                          ★  Worker起動/登録
│     │  ├─ main.go                            ★  Worker起動/metrics
│     │  ├─ register.go                        ★  WF/Activity登録
│     │  └─ activities.go                      ★  /internal 呼出し/冪等送信
│     ├─ domain/                               △
│     │  └─ .gitkeep                           △
│     └─ infrastructure/                       △
│        └─ .gitkeep                           △
├─ platform/                                   ★  インフラ定義/初期化
│  ├─ temporal/                                ★  Temporal設定
│  │  ├─ search-attributes.hcl                 ★  SA=4キー(space-id/corr-id/stage-no/run-state)
│  │  ├─ namespace.sh                          ★  Namespace/SA 初期化スクリプト
│  │  ├─ docker-compose.dev.yml                ★  dev: server+ui
│  │  └─ README.md                             ★  登録手順/注意事項
│  └─ libsql/                                  ★  業務DB(SSOT)
│     ├─ docker-compose.dev.yml                ★  ローカル sqld
│     ├─ migrate.sh                            ★  migrations 適用スクリプト
│     └─ migrations/                           ★  DDL履歴
│        ├─ 0001_init.sql                      ★  runs/events/kpi 基本テーブル
│        └─ 0002_kpi.sql                       ★  KPI拡張
├─ .artifacts/                                 ◇  非コミット生成物
│  ├─ manifests/                               ◇  flake→manifest 生成結果
│  │  ├─ features/<domain>/<feature>/manifest.cue
│  │  └─ deployables/<tier>/<name>/manifest.cue
│  └─ reports/                                 ◇  監査/検証レポート
│     ├─ summary.json                          ◇  監査サマリ
│     ├─ sbom.json                             ◇  SBOM（リリース時）
│     ├─ cve.json                              ◇  CVE（週次+リリース前）
│     ├─ parity.json                           ◇  パリティ検証結果
│     ├─ plan-diff.json                        ◇  依存DAG差分
│     ├─ contract-diff.json                    ◇  契約互換性チェック
│     ├─ determinism.json                      ◇  決定性検証
│     └─ secrets.json                          ◇  Secrets検出結果
├─ tools/                                      ★  ビルド/検証ツール
│  ├─ bridge/
│  │  └─ flake2manifest                        ★  flake→manifest.cue決定的生成
│  ├─ generator/
│  │  ├─ gen                                   ★  SSOT→gen/dist生成
│  │  └─ check                                 ★  指紋検証
│  ├─ security/                                ★  セキュリティツール群
│  │  ├─ secrets.sh                            ★  Secrets検出（P0必須）
│  │  ├─ sbom.sh                               ★  SBOM生成（P1）
│  │  └─ cve_scan.sh                           ★  CVE突合（P2）
│  ├─ gates/                                   ★  CI検証ゲート（失敗で止める）
│  │  ├─ parity.cue                            ★  modules ⊆ flake（consumes/provides）
│  │  ├─ plan-diff.cue                         ★  孤児/未提供/循環
│  │  ├─ contract-diff.cue                     ★  SemVer破壊検出
│  │  ├─ cap-dup.cue                           ★  capability重複検出
│  │  ├─ determinism.cue                       ★  決定性チェック
│  │  ├─ secrets.cue                           ★  Secrets検出（P0必須）
│  │  ├─ mask.cue                              ★  PII検出/マスク
│  │  ├─ license.cue                           ★  ライセンスチェック
│  │  └─ cve.cue                               ★  CVE突合
│  ├─ graph/                                   △  可視化
│  │  └─ build-graph.sh                        △  契約DAG可視化
│  └─ paths-filter/                            △  変更検出
│     └─ filters.yml                           △  changed-only 実行ルール
├─ policy/                                     ★  規約/ルール（CUE）
│  └─ cue/
│     ├─ config.cue                            ★  ポリシーフラグ（fail/warn/off）
│     ├─ schemas/                              ★  厳格スキーマ
│     │  ├─ manifest.cue                       ★  manifest厳格スキーマ（未知キー禁止）
│     │  ├─ module.cue                         ★  module厳格スキーマ
│     │  └─ responsibility.cue                 ★  responsibility厳格スキーマ
│     └─ rules/                                ★  検証ルール
│        ├─ strict.cue                         ★  URI必須/SA4固定/GW-DB書込禁止
│        ├─ parity.cue                         ★  宣言↔実装の部分集合検証
│        ├─ determinism.cue                    ★  決定性チェック
│        ├─ secrets.cue                        ★  Secrets検出（P0必須）
│        ├─ mask.cue                           ★  PII検出
│        ├─ license.cue                        ★  ライセンスチェック
│        └─ cve.cue                            ★  CVE突合
├─ ci/                                         ★  CI設定/スクリプト
│  ├─ workflows/                               ★  GitHub Actions workflows
│  │  ├─ ci.yml                                ★  メインCI（直列: index→flake2manifest→vet→gen→gates→runners）
│  │  ├─ cve-weekly.yml                        ★  週次CVEスキャン
│  │  ├─ release-preflight.yml                 ★  リリース前検証（SBOM+CVE）
│  │  ├─ nightly.yml                           △  夜間ビルド
│  │  └─ quarantine.yml                        △  隔離テスト
│  ├─ config/                                  ★  CI設定
│  │  ├─ phases.yaml                           ★  実行フェーズ定義
│  │  └─ pipeline.yaml                         ★  パイプライン定義
│  ├─ e2e/
│  │  └─ e2e-smoke.sh                          ★  fs:// 最短経路スモークテスト
│  ├─ reports/                                 ◇  CI実行レポート
│  └─ artifacts/                               ◇  CI成果物
└─ env/                                        △  環境テンプレート
   └─ .gen/                                    ◇  生成された環境設定
      ├─ dev.env                               ◇
      └─ prod.env                              ◇
```

---

## 構成原則（ADR 0.10.12準拠）

### 命名規則
- **kebab-case** 統一（ディレクトリ・ファイル名）
- SA（Search Attributes）: `space-id`, `corr-id`, `stage-no`, `run-state`（4キー固定）

### 階層ルール
- **1 feature = 1 flake**: `features/<name>/flake.nix`
- **1 deployable = 1 flake**: `deployables/<name>/flake.nix`
- **DDD3層必須**: `application/`, `domain/`, `infrastructure/`（空なら `.gitkeep`）
- **`src/` 禁止**: 余分な中間層を排除（KISS/YAGNI）

### 責務分離
- **GW（Gateway）**: 無状態、揮発Map、逆プロキシ、内部API(2本)のみ
- **WF（Workflow）**: SSOT唯一の書込主体、SA更新一極化（`setStage()`）
- **Worker（Activity）**: 外部I/O、冪等送信
- **SSOT（libsql）**: WFのみが書込、runs/events/kpi

### 禁止事項（CUEポリシで強制）
- ❌ **dirPath使用禁止**: URI必須（`fs://`, `git://`, etc.）
- ❌ **SA拡張禁止**: 4キー固定（`space-id/corr-id/stage-no/run-state`）
- ❌ **GWのDB書込禁止**: 読み取り専用（WFのみが書込）

---

## API構成（最小化）

### 外部API（/api）
- `POST /jobs/start`: ジョブ開始（uri必須）
- `POST /sessions/:id/ack`: セッション承認
- `POST /sessions/:id/snooze`: セッション延期
- `POST /sessions/:id/cancel`: セッションキャンセル
- `GET /jobs/:id/status`: ジョブ状態取得

### 内部API（/internal）
- `POST /opencode/ensure`: OpenCodeインスタンス確保（GW→起動管理）
- `POST /wf/task-completed`: タスク完了通知（Worker→WF、冪等）

---

## Search Attributes（SA）遷移

| stage-no | run-state | 意味 |
|----------|-----------|------|
| 0 | PENDING | 受付 |
| 1 | RUNNING | 進行 |
| 2 | WAITING | 待機（ACK待ち） |
| 3 | COMPLETED | 完了 |
| - | REPLACED | 置換済み（`replace: true`時） |

---

## 更新履歴

- **2025-10-23**: ADR 0.10.12適用、Orchestration v4.1b構成に全面更新（`src/`削除、DDD3層統一、SA4キー固定）
- **抽象構造**: ADR 0.10.8-0.10.11に記載（本ファイルは最新の具体構造のみ）

---

**生成方法**: 手動更新（将来的に `tools/generator` で自動生成予定）
