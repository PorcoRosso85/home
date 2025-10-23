# Repository Tree (Latest Design Only)

> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

**Last Updated**: 2025-10-23 (JST)
**対応ADR**: docs/adr/adr-0.11.0.md
**運用原則**: この tree は宣言。未記載 = 削除。今回は再配置のみでデグレ無しを厳守。

---

## 最新ツリー（ADR 0.11.0 — 4層＋SSOT）

> 凡例: # = コメント（各行の責務説明）

```
repo/                                               # ルート。単一flake/lockの支点
├─ flake.nix                                        # ルートflake：単一pin・出力集約・forAllSystems
├─ flake.lock                                       # 唯一のlock（全sub-flakeはfollowsで追随）
├─ README.md                                        # 規約/層責務/PRチェックリストの要約
├─ contracts/                                       # 契約ルート（SSOTのみ）
│  └─ ssot/                                         # SSOT固定ディレクトリ
│     ├─ video/                                     # video境界づけ文脈の契約
│     │  ├─ schema.sql                              # DBスキーマ（唯一の正）
│     │  ├─ events.cue                              # ドメインイベント契約
│     │  └─ openapi.yaml                            # 外部API契約
│     └─ search/                                    # search境界づけ文脈の契約
│        ├─ schema.sql                              # DBスキーマ（唯一の正）
│        └─ search.proto                            # gRPC/IDL契約
├─ infra/                                           # 実行基盤・SDK・依存宣言の唯一の場所
│  ├─ flake.nix                                     # devShells/checks（ruff/pytest/deadnix/statix）を集約提供
│  ├─ runtimes/                                     # ランタイム束（FW/ツール類を固定）
│  │  ├─ python-django/                             # Django系ランタイム
│  │  │  ├─ flake.nix                               # ランタイム出力（packages.runtimes.python-django）
│  │  │  └─ constraints.txt                         # pip系制約（pin）
│  │  ├─ python-fastapi/                            # FastAPI系ランタイム
│  │  │  ├─ flake.nix                               # 出力・devShell
│  │  │  └─ constraints.txt                         # pin
│  │  ├─ python-ffmpeg/                             # FFmpeg/映像合成ランタイム
│  │  │  ├─ flake.nix                               # 出力・devShell
│  │  │  └─ constraints.txt                         # pin
│  │  └─ python-ml/                                 # ML/推論ランタイム
│  │     ├─ flake.nix                               # 出力・devShell
│  │     └─ constraints.txt                         # pin
│  └─ adapters/                                     # Port実装（外部I/O）群
│     ├─ storage/                                   # ストレージAdapter群
│     │  ├─ r2/                                     # R2実装
│     │  │  ├─ flake.nix                            # packages.adapters.storage-r2
│     │  │  └─ requirements.in                      # 依存宣言（constraintsに取り込み）
│     │  ├─ s3/                                     # S3実装
│     │  │  ├─ flake.nix                            # packages.adapters.storage-s3
│     │  │  └─ requirements.in                      # 依存宣言
│     │  └─ drive/                                  # Drive実装
│     │     ├─ flake.nix                            # packages.adapters.storage-drive
│     │     └─ requirements.in                      # 依存宣言
│     ├─ db/                                        # DBアクセスAdapter群
│     │  ├─ libsql/                                 # libsql実装
│     │  │  ├─ flake.nix                            # packages.adapters.db-libsql
│     │  │  └─ requirements.in                      # 依存宣言
│     │  └─ postgres/                               # Postgres実装
│     │     ├─ flake.nix                            # packages.adapters.db-postgres
│     │     └─ requirements.in                      # 依存宣言
│     ├─ queue/                                     # キュー/ワークフローAdapter群
│     │  ├─ temporal/                               # Temporal実装
│     │  │  ├─ flake.nix                            # packages.adapters.queue-temporal
│     │  │  └─ requirements.in                      # 依存宣言
│     │  └─ celery/                                 # Celery実装
│     │     ├─ flake.nix                            # packages.adapters.queue-celery
│     │     └─ requirements.in                      # 依存宣言
│     ├─ tts/                                       # 音声合成Adapter群
│     │  ├─ azure/                                  # Azure TTS実装
│     │  │  ├─ flake.nix                            # packages.adapters.tts-azure
│     │  │  └─ requirements.in                      # 依存宣言
│     │  └─ polly/                                  # AWS Polly実装
│     │     ├─ flake.nix                            # packages.adapters.tts-polly
│     │     └─ requirements.in                      # 依存宣言
│     ├─ encoder/                                   # エンコードAdapter群
│     │  └─ ffmpeg/                                 # FFmpeg実装
│     │     ├─ flake.nix                            # packages.adapters.encoder-ffmpeg
│     │     └─ requirements.in                      # 依存宣言
│     ├─ ml/                                        # ML推論Adapter群
│     │  ├─ openai/                                 # OpenAI実装
│     │  │  ├─ flake.nix                            # packages.adapters.ml-openai
│     │  │  └─ requirements.in                      # 依存宣言
│     │  └─ azure-openai/                           # Azure OpenAI実装
│     │     ├─ flake.nix                            # packages.adapters.ml-azure-openai
│     │     └─ requirements.in                      # 依存宣言
│     └─ opencode/                                  # 旧orchestration相当の実装の受け皿
│        └─ autopilot/                              # Autopilot実装（名称継承）
│           ├─ flake.nix                            # packages.adapters.opencode-autopilot
│           └─ requirements.in                      # 依存宣言
├─ domains/                                         # 純粋ロジック/Portのみ（外部非接続）
│  ├─ video/                                        # videoドメイン
│  │  ├─ flake.nix                                  # nixpkgsのみfollows／devShell禁止
│  │  ├─ video/                                     # パッケージ直置き（src無し規約）
│  │  ├─ ports/                                     # 抽象Port定義
│  │  │  ├─ storage.py                              # Storage Port（put/get等）
│  │  │  ├─ tts.py                                  # TTS Port（synthesize等）
│  │  │  └─ encoder.py                              # Encoder Port（compose/transcode等）
│  │  └─ tests/                                     # ドメイン純ユニットテスト（ポートモック）
│  └─ search/                                       # searchドメイン
│     ├─ flake.nix                                  # nixpkgsのみfollows／devShell禁止
│     ├─ search/                                    # パッケージ直置き
│     ├─ ports/                                     # 抽象Port定義
│     │  ├─ index.py                                # Index Port
│     │  └─ repo.py                                 # Repository Port
│     └─ tests/                                     # 純ユニットテスト
├─ apps/                                            # ユースケース/編成（DI対象）
│  ├─ video/                                        # videoアプリケーション層
│  │  ├─ flake.nix                                  # apps.<sys>.video（type=app）を出力
│  │  ├─ usecases/                                  # Command/Query/Handler実装
│  │  ├─ workflows/                                 # 複数usecaseの編成（旧orchestrationの置き場）
│  │  ├─ dto.py                                     # アプリ内DTO（Transport非依存）
│  │  ├─ manifest.cue                               # 入出力/依存宣言（構成）
│  │  └─ pipeline.cue                               # パイプライン定義（段構成）
│  └─ search/                                       # searchアプリケーション層
│     ├─ flake.nix                                  # apps.<sys>.search（type=app）を出力
│     ├─ usecases/                                  # Command/Query/Handler実装
│     ├─ dto.py                                     # アプリ内DTO
│     └─ manifest.cue                               # 構成
├─ interfaces/                                      # 入口（HTTP/gRPC/CLI/Web）。wireでDI
│  ├─ http-video-django/                            # Django/DRFエントリ（HTTP）
│  │  ├─ flake.nix                                  # apps.<sys>.interface.http-video-django（type=app）
│  │  ├─ project/                                   # Django設定/ASGI
│  │  │  ├─ settings.py                             # 設定（環境差分はenv overlayで）
│  │  │  ├─ urls.py                                 # ルーティング
│  │  │  └─ asgi.py                                 # ASGIエントリ
│  │  ├─ api/                                       # Transport DTO/Serializer/Views
│  │  │  ├─ views.py                                # HTTPハンドラ（apps呼び出し）
│  │  │  ├─ serializers.py                          # 入出力バリデーション
│  │  │  └─ dto.py                                  # Transport DTO
│  │  ├─ wire.py                                    # Composition Root（PortへAdapter注入）
│  │  ├─ generated/                                 # OpenAPI等の生成物
│  │  └─ tests/                                     # API契約テスト
│  ├─ grpc-search/                                  # gRPCエントリ
│  │  ├─ flake.nix                                  # apps.<sys>.interface.grpc-search（type=app）
│  │  ├─ server/                                    # gRPCサーバ起動
│  │  │  └─ main.py                                 # メイン
│  │  ├─ wire.py                                    # DI
│  │  ├─ generated/                                 # proto生成物
│  │  └─ tests/                                     # 契約テスト
│  ├─ cli-video/                                    # CLIエントリ
│  │  ├─ flake.nix                                  # apps.<sys>.interface.cli-video（type=app）
│  │  ├─ main.py                                    # CLI本体（apps呼び出し）
│  │  ├─ wire.py                                    # DI
│  │  └─ tests/                                     # CLIテスト
│  ├─ http-opencode-gateway/                        # Orchestration HTTPエントリ（旧deployables/opencode-gateway）
│  │  ├─ flake.nix                                  # apps.<sys>.interface.http-opencode-gateway（type=app）
│  │  ├─ api/                                       # API handlers（/api, /internal）
│  │  │  ├─ main.go                                 # HTTPサーバ起動
│  │  │  └─ routes.go                               # ルーティング定義
│  │  ├─ wire.go                                    # DI（Port→Adapter注入）
│  │  └─ tests/                                     # API契約テスト
│  └─ web-search-next/                              # Next.js UI
│     ├─ flake.nix                                  # apps.<sys>.interface.web-search-next（type=app）
│     ├─ app/                                       # UIコード
│     ├─ wire.ts                                    # APIクライアント/DI
│     └─ tests/                                     # E2E/契約テスト
├─ policy/                                          # 構造ガード（CUE）
│  └─ cue/
│     ├─ schemas/                                   # スキーマ定義
│     │  ├─ manifest.cue                            # manifest型
│     │  ├─ deps.cue                                # 依存許可リスト
│     │  ├─ naming.cue                              # 命名規約（ハイフン/出力＝パス）
│     │  └─ layout.cue                              # 配置規約（宣言ファイルの許可場所等）
│     └─ rules/                                     # 実際の検査ルール
│        ├─ strict.cue                              # 依存方向：interfaces→apps→domains→contracts / apps→infra
│        ├─ no-deps-outside-infra.cue               # 依存宣言はinfra配下のみ許可
│        ├─ forbidden-imports.cue                   # domainsで外部FW/SDK import禁止
│        └─ outputs-naming.cue                      # 出力名＝パス名/ハイフン統一
├─ ci/                                              # CI定義
│  └─ workflows/
│     ├─ apps-video.yml                             # apps/video のビルド/テスト
│     ├─ http-video.yml                             # http-video-django のCI
│     ├─ grpc-search.yml                            # grpc-search のCI
│     └─ web-search.yml                             # web-search-next のCI
└─ docs/                                            # ドキュメント
   ├─ adr/
   │  ├─ adr-0.10.8.md                              # SSOT-first & thin manifest
   │  ├─ adr-0.10.10.md                             # Flake-driven manifest
   │  ├─ adr-0.10.11.md                             # consumes/Secrets/SBOM/CVE
   │  ├─ adr-0.10.12.md                             # Status: Superseded（履歴）
   │  └─ adr-0.11.0.md                              # 本ADR（4層＋SSOT）
   ├─ tree.md                                       # このファイル（最新構成の単一真実）
   └─ architecture/
      ├─ context.mmd                                # コンテキスト図
      └─ sequence.mmd                               # 代表シーケンス図
```

---

## 構成原則（ADR 0.11.0準拠）

### 4層構造

```
interfaces → apps → domains → contracts
              ↓
           infra
```

### 各層の責務

| 層 | 責務 | 依存先 | 禁止事項 |
|---|------|--------|---------|
| **interfaces/** | 入口（HTTP/gRPC/CLI/Web）、wire.pyでDI | apps + infra.runtimes | ビジネスロジック記述 |
| **apps/** | ユースケース/編成、型変換 | domains + infra.adapters | 外部I/O直接呼出 |
| **domains/** | 純粋ロジック、Port定義 | contracts | 外部FW/SDK import |
| **contracts/** | DDL/IDL/イベント定義（SSOT） | なし | 実装コード |
| **infra/** | ランタイム/SDK/Adapter実装 | なし（leaf） | ビジネスロジック |

### 命名規則

- **kebab-case統一**: ディレクトリ/ファイル名
- **出力名 = パス名**: Flake出力とパス名が一致（ズレはCI fail）

### 依存宣言の一元化

**原則**: 依存宣言は `infra/` 配下のみ許可

- `infra/runtimes/*/constraints.txt`
- `infra/adapters/*/*/requirements.in`

### Flake運用

- **ルート単一flake.lock**: 全sub-flakeは `inputs.nixpkgs.follows = "nixpkgs"`
- **devShells集約**: `infra/flake.nix` で ruff/pytest/deadnix/statix を提供
- **domains/のdevShell禁止**: 外部非接続を保証

---

## 再配置ルール（重要）

### 許可される操作
- ✅ `git mv`（ディレクトリ/ファイル移動）
- ✅ importパス置換（移動に伴うパス修正）
- ✅ flake出力名の整合（出力名=パス名）
- ✅ `wire.py` のDI差し替え（Port→Adapter注入）

### 禁止される操作
- ❌ 関数/クラスシグネチャ変更
- ❌ 新規機能追加
- ❌ `contracts/ssot/**` の変更（schema.sql/events.cue/openapi.yaml/proto）
- ❌ 依存追加/更新（constraints.txt/requirements.in）

### CI必須条件
1. ✅ 全テスト不変緑（ユニット/統合/契約/E2E）
2. ✅ `nix flake check` 緑
3. ✅ `policy/cue` 違反0
4. ✅ `contracts/` 差分なし

---

## 移行マッピング（0.10.12 → 0.11.0）

| 旧パス（0.10.12） | 新パス（0.11.0） | 理由 |
|-----------------|----------------|------|
| `features/opencode-autopilot/` | `infra/adapters/opencode/autopilot/` | Port実装（外部システム） |
| `deployables/opencode-gateway/` | `interfaces/http-opencode-gateway/` | HTTPエントリポイント |
| `deployables/opencode-worker/` | `apps/video/workflows/` + `infra/adapters/queue/temporal/` | ワークフロー編成+実装分離 |
| `platform/temporal/` | `infra/adapters/queue/temporal/` | インフラAdapter |
| `platform/libsql/` | `infra/adapters/db/libsql/` | DB Adapter |

---

## 更新履歴

- **2025-10-23**: ADR 0.11.0適用、4層構造への完全移行（再配置のみ、デグレなし）
- **Supersedes**: ADR 0.10.12（Orchestration v4.1b）

---

**生成方法**: 手動更新（将来的に `tools/generator` で自動生成予定）
