# Repository Tree (Latest Design Only)

> ADR本文にツリーは書かない。本ファイルのみ最新設計を更新。
> 5原則（SRP/KISS/YAGNI/SOLID/DRY）を徹底。必要になるまで実装しない（YAGNI）。

**Last Updated**: 2025-10-25 (JST)
**対応ADR**: docs/adr/adr-0.11.3.md, docs/adr/adr-0.11.4.md, docs/adr/adr-0.11.5.md, docs/adr/adr-0.11.6.md, docs/adr/adr-0.11.7.md, docs/adr/adr-0.11.8.md
**運用原則**: この tree は宣言。未記載 = 削除。今回は再配置のみでデグレ無しを厳守。

---

## 最新ツリー（ADR 0.11.3 — 最終形：0.11.2 + IaC統合）

> 凡例: # = コメント（各行の責務説明）

```
repo/                                               # ルート（単一flake/lock）
├─ flake.nix                                        # ルートflake：出力集約/forAllSystems
├─ flake.lock                                       # 単一lock（sub-flakeはfollows）
├─ README.md                                        # 規約/層責務/PRチェックリスト要約
├─ contracts/                                       # SSOT（実装禁止）
│  └─ ssot/
│     ├─ video/                                     # 例：video境界づけ文脈
│     │  ├─ schema.sql                              # DBスキーマ（唯一の正）
│     │  ├─ events.cue                              # ドメインイベント契約
│     │  └─ openapi.yaml                            # 外部API契約
│     └─ search/                                    # 例：search境界づけ文脈
│        ├─ schema.sql                              # DBスキーマ（唯一の正）
│        └─ search.proto                            # gRPC/IDL契約
├─ infra/                                           # 依存/SDK/ランタイム/アダプタ/プロビジョニングの唯一の置き場
│  ├─ flake.nix                                     # devShells/checks集約（ruff/pytest等）
│  ├─ runtimes/                                     # FW/ツール束（pin）
│  │  ├─ python-django/
│  │  │  ├─ flake.nix                               # ランタイム出力（packages.runtimes.python-django）
│  │  │  └─ constraints.txt                         # pip系制約（pin）
│  │  ├─ python-fastapi/
│  │  │  ├─ flake.nix                               # 出力・devShell
│  │  │  └─ constraints.txt                         # pin
│  │  ├─ python-ffmpeg/
│  │  │  ├─ flake.nix                               # 出力・devShell
│  │  │  └─ constraints.txt                         # pin
│  │  └─ python-ml/
│  │     ├─ flake.nix                               # 出力・devShell
│  │     └─ constraints.txt                         # pin
│  ├─ adapters/                                     # Port実装（外部I/O）群
│  │  ├─ storage/                                   # ストレージAdapter群（既定＝R2/、CI＝MinIO）
│  │  │  ├─ r2/                                     # R2実装（本番既定・唯一のクラウドストレージ）
│  │  │  │  ├─ flake.nix                            # packages.adapters.storage-r2
│  │  │  │  └─ requirements.in                      # 依存宣言（constraintsに取り込み）
│  │  │  ├─ drive/                                  # Drive実装（代替）
│  │  │  │  ├─ flake.nix                            # packages.adapters.storage-drive
│  │  │  │  └─ requirements.in                      # 依存宣言
│  │  │  └─ (s3/)                                   # ❌ S3廃止済み・復活禁止（ADR 0.11.1/0.11.3）
│  │  ├─ db/                                        # DBアクセスAdapter群
│  │  │  ├─ libsql/                                 # libsql実装
│  │  │  │  ├─ flake.nix                            # packages.adapters.db-libsql
│  │  │  │  └─ requirements.in                      # 依存宣言
│  │  │  └─ postgres/                               # Postgres実装
│  │  │     ├─ flake.nix                            # packages.adapters.db-postgres
│  │  │     └─ requirements.in                      # 依存宣言
│  │  ├─ queue/                                     # キュー/ワークフローAdapter群
│  │  │  ├─ temporal/                               # Temporal実装
│  │  │  │  ├─ flake.nix                            # packages.adapters.queue-temporal
│  │  │  │  └─ requirements.in                      # 依存宣言
│  │  │  └─ celery/                                 # Celery実装
│  │  │     ├─ flake.nix                            # packages.adapters.queue-celery
│  │  │     └─ requirements.in                      # 依存宣言
│  │  ├─ tts/                                       # 音声合成Adapter群
│  │  │  ├─ azure/                                  # Azure TTS実装
│  │  │  │  ├─ flake.nix                            # packages.adapters.tts-azure
│  │  │  │  └─ requirements.in                      # 依存宣言
│  │  │  └─ polly/                                  # AWS Polly実装
│  │  │     ├─ flake.nix                            # packages.adapters.tts-polly
│  │  │     └─ requirements.in                      # 依存宣言
│  │  ├─ encoder/                                   # エンコードAdapter群
│  │  │  └─ ffmpeg/                                 # FFmpeg実装
│  │  │     ├─ flake.nix                            # packages.adapters.encoder-ffmpeg
│  │  │     └─ requirements.in                      # 依存宣言
│  │  ├─ ml/                                        # ML推論Adapter群
│  │  │  ├─ openai/                                 # OpenAI実装
│  │  │  │  ├─ flake.nix                            # packages.adapters.ml-openai
│  │  │  │  └─ requirements.in                      # 依存宣言
│  │  │  └─ azure-openai/                           # Azure OpenAI実装
│  │  │     ├─ flake.nix                            # packages.adapters.ml-azure-openai
│  │  │     └─ requirements.in                      # 依存宣言
│  │  └─ opencode/                                  # 旧orchestration相当の実装の受け皿
│  │     └─ autopilot/                              # Autopilot実装（名称継承）
│  │        ├─ flake.nix                            # packages.adapters.opencode-autopilot
│  │        └─ requirements.in                      # 依存宣言
│  ├─ presentation-runtime/                         # プレゼンテーション表示ランタイム（旧 infra/sdk/ui-wc）
│  │  └─ x-deck/                                    # Web Componentランタイム
│  │     ├─ deck.ts                                 # ブラウザで動く表示・遷移制御
│  │     ├─ deck.css                                # スタイル
│  │     ├─ tsconfig.json                           # TypeScript設定
│  │     └─ flake.nix                               # packages.presentation-runtime.x-deck
│  ├─ content-build-tools/                          # コンテンツビルドツール群（旧 infra/sdk/md-tools）
│  │  ├─ shared/                                    # 共通ロジック（DRY）
│  │  │  ├─ out-path.mjs                            # 出力パス計算
│  │  │  ├─ frontmatter.mjs                         # frontmatter解析
│  │  │  └─ metadata.mjs                            # メタデータ抽出
│  │  ├─ md2html/                                   # MD → HTML/sections 変換
│  │  │  ├─ cli.mjs                                 # CLIエントリポイント
│  │  │  └─ pipeline/                               # 変換パイプライン
│  │  │     ├─ remark-frag.mjs                      # remarkプラグイン（フラグメント分割）
│  │  │     ├─ remark-split.mjs                     # remarkプラグイン（セクション分割）
│  │  │     ├─ remark-wc-map.mjs                    # remarkプラグイン（WCマッピング）
│  │  │     └─ rehype-shiki.mjs                     # rehypeプラグイン（Shiki焼き込み）
│  │  ├─ mmd2svg/                                   # Mermaid → SVG 変換
│  │  │  └─ cli.mjs                                 # CLIエントリポイント（CI側で生成）
│  │  └─ pdf-export/                                # HTML → PDF 変換
│  │     └─ cli.mjs                                 # CLIエントリポイント（Playwright使用）
│  └─ provisioning/                                 # IaCの単一の正（OpenTofu運用域）【0.11.3新規追加】
│     ├─ modules/                                   # クラウドリソース宣言（Tofu module定義）
│     │  ├─ storage_bucket/                         # R2バケット作成module
│     │  │  ├─ main.tf                              # module本体
│     │  │  ├─ variables.tf                         # 入力変数
│     │  │  └─ outputs.tf                           # 出力定義
│     │  ├─ cdn_distribution/                       # CDN配信設定module
│     │  │  ├─ main.tf
│     │  │  ├─ variables.tf
│     │  │  └─ outputs.tf
│     │  └─ compute_instance/                       # コンピュートインスタンスmodule
│     │     ├─ main.tf
│     │     ├─ variables.tf
│     │     └─ outputs.tf
│     ├─ environments/                              # 環境別変数セット
│     │  ├─ dev/                                    # 開発環境設定
│     │  │  ├─ terraform.tfvars                     # 変数値
│     │  │  └─ backend.tf                           # ローカルstate設定
│     │  ├─ staging/                                # ステージング環境設定
│     │  │  ├─ terraform.tfvars                     # 変数値
│     │  │  └─ backend.tf                           # R2バックエンド設定
│     │  └─ prod/                                   # 本番環境設定
│     │     ├─ terraform.tfvars                     # 変数値
│     │     └─ backend.tf                           # R2バックエンド設定（暗号化・ロック有効）
│     ├─ state/                                     # 開発ローカルstate置き場（.gitignore対象）
│     ├─ outputs/                                   # tofu output -json の生データ（CUE検証前）
│     ├─ cue/                                       # 出力値のCUEスキーマと検証
│     │  ├─ schemas/                                # outputスキーマ（型定義）
│     │  │  ├─ storage.cue                          # storage出力の型定義
│     │  │  ├─ cdn.cue                              # CDN出力の型定義
│     │  │  └─ compute.cue                          # compute出力の型定義
│     │  └─ checks.cue                              # 検証ロジック（全outputの整合性チェック）
│     ├─ scripts/                                   # 公式ラッパスクリプト（統一インタフェース）
│     │  ├─ plan.sh                                 # tofu plan/apply ラッパ
│     │  ├─ export-env.sh                           # 検証済みoutput → .env生成
│     │  └─ verify.sh                               # cue vet / diff検証
│     ├─ flake.nix                                  # tofu/cue/sops等のバージョン固定
│     └─ README.md                                  # 運用規約・R2 backendの方針・公式フロー説明
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
│  ├─ web-search-next/                              # Next.js UI
│  │  ├─ flake.nix                                  # apps.<sys>.interface.web-search-next（type=app）
│  │  ├─ app/                                       # UIコード
│  │  ├─ wire.ts                                    # APIクライアント/DI
│  │  └─ tests/                                     # E2E/契約テスト
│  ├─ docs-build-cli/                               # ドキュメント生成CLI（旧 cli-docs）
│  │  ├─ flake.nix                                  # apps.<sys>.interface.docs-build-cli（type=app）
│  │  └─ main.mjs                                   # content-build-tools の md2html/mmd2svg/pdf-export を呼ぶ
│  └─ docs-static-site/                             # 静的サイト配信interface（旧 web-docs-vanilla）
│     ├─ flake.nix                                  # apps.<sys>.interface.docs-static-site（type=app）
│     ├─ src/
│     │  └─ index.html                              # エントリHTML
│     ├─ public/                                    # 静的資産
│     └─ dist/                                      # CDN/Pages配信用（.gitignore対象）
│        ├─ index.html                              # 生成されたHTML
│        ├─ sections/                               # セクション分割HTML
│        └─ assets/                                 # CSS/JS/画像等
├─ policy/                                          # 構造ガード（CUE）
│  └─ cue/                                          # リポジトリ構造・依存ルールの静的検証
│     ├─ schemas/                                   # スキーマ定義
│     │  ├─ deps.cue                                # 依存許可リスト（provisioning追加）
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
│     ├─ web-search.yml                             # web-search-next のCI
│     ├─ docs-build.yml                             # docs-build-cli を叩いてプリレンダ実行
│     ├─ slides-export.yml                          # pdf-export を叩いてPDF吐く
│     └─ infra-deploy.yml                           # infra/provisioning/ からTofuデプロイ（0.11.3追加）
└─ docs/                                            # ドキュメント
   ├─ adr/
   │  ├─ adr-0.10.8.md                              # SSOT-first & thin manifest
   │  ├─ adr-0.10.10.md                             # Flake-driven manifest
   │  ├─ adr-0.10.11.md                             # consumes/Secrets/SBOM/CVE
   │  ├─ adr-0.10.12.md                             # Status: Superseded（履歴）
   │  ├─ adr-0.11.0.md                              # Status: Superseded（履歴）
   │  ├─ adr-0.11.1.md                              # Status: Superseded（履歴）
   │  ├─ adr-0.11.2.md                              # Status: Superseded（履歴）
   │  ├─ adr-0.11.3.md                              # 最終形：0.11.2 + IaC統合
   │  ├─ adr-0.11.4.md                              # sops-nix / flake細粒度 / manifest guard / Terranix
   │  ├─ adr-0.11.5.md                              # Secrets=唯一入口 / CUE=SSOT / leaf分割 / Guard方針
   │  ├─ adr-0.11.6.md                              # Finalize Secrets/Guard/IaC/Zoning policies
   │  ├─ adr-0.11.7.md                              # DoD整合性確認の完了（CUEガバナンス）
   │  └─ adr-0.11.8.md                              # Manifest責務定義 & Capabilityガバナンス方針
   ├─ tree.md                                       # このファイル（最新構成の単一真実）
   ├─ architecture/
   │  ├─ context.mmd                                # コンテキスト図
   │  └─ sequence.mmd                               # 代表シーケンス図
   ├─ slides/                                       # プレゼンテーションソース
   │  └─ example.md                                 # Markdownスライド
   └─ dist/                                         # 生成結果（.gitignore対象）
```

---

## 運用方針（骨子）

このファイルは**現状構成の骨格宣言**のみを扱う。手順や詳細は**ADR参照**。

### IaC / デプロイ（要約）
- **Terranix → OpenTofu**で環境別（prod/stg/dev）のIaCを生成。
- **remote state は R2(S3互換)**、ロックと環境分離を前提化。
- **Secrets は sops-nix**で暗号化。平文コミット不可。復号はactivation時に実施。
- **Secrets = 唯一のエントリポイント（手動管理）**。外部金庫・R2バックアップは当面不採用（詳細: ADR 0.11.5）。

### Manifest Guard（要約）
- 各サービスの実使用infraは**flake出力(=manifest)**で生成。
- サービス側の**allowlist**と比較して逸脱を検出（将来CIでfail）。
- **flakeはleaf出力**へ細分化し、サービスは必要leafのみ束ねる。
- **※ manifestはflake生成(CUE)。リポに固定ファイルは置かない（VCS非追跡）。**
- **CUE=SSOT**。必要時のみ `CUE → (sh/json/yaml)` 生成。逆方向禁止（詳細: ADR 0.11.5）。
- **出力形式=CUE固定、生成物はVCS非追跡**（詳細: ADR 0.11.6）。

### Logs / 観測（要約）
- **長期保管はR2**（SaaS不使用）。Loki等は任意の可視化レイヤ（詳細: ADR 0.11.6）。

### Zoning（要約）
- **当面はzoneラベルで管理**、stable昇格後に物理移動（詳細: ADR 0.11.6）。

> 注: 具体的コマンドやコード例は tree には置かない（ADR 0.11.4/0.11.5/0.11.6 を参照）。

---

## 構成原則（ADR 0.11.3/0.11.4/0.11.5/0.11.6/0.11.7/0.11.8準拠）

### 4層構造（変更なし）

```
interfaces → apps → domains → contracts
              ↓
           infra
```

### 命名規則

**原則**: `<ドメイン>-<用途>-<形態>`

| 例 | 意味 |
|----|------|
| `docs-build-cli` | docsをbuildするCLI |
| `docs-static-site` | docsを静的サイトとして配信 |
| `presentation-runtime` | プレゼンテーション表示のランタイム |
| `content-build-tools` | コンテンツビルドのツール群 |
| `provisioning` | クラウドリソースのプロビジョニング |

### infra/の最終構造

```
infra/
├─ runtimes/              # ランタイム環境のバージョン固定
├─ adapters/              # 作成済みリソースへの「接続」コード（SDK）
├─ presentation-runtime/  # ランタイム資産（旧 sdk/ui-wc）
├─ content-build-tools/   # ビルドツール（旧 sdk/md-tools）
└─ provisioning/          # クラウドリソースの「作成」宣言（OpenTofu）【0.11.3追加】
```

**provisioning vs adapters の境界**:
- **provisioning**: クラウドリソースを**作る**層（OpenTofu）
- **adapters**: 作成済みリソースに**つなぐ**層（SDK/クライアント）
- **データの流れ**: `provisioning → (tofu output / .env) → adapters`

### dist配置ルール（0.11.2継承）

- ✅ **interfaces/** の静的配信interface **のみ**が `dist/` を持つ
- ❌ **infra/** は `dist/` を持たない（配信元ではない）

### CUEの役割分担（0.11.3明文化）

| ディレクトリ | 責務 | 検証対象 |
|-------------|------|---------|
| `policy/cue/` | リポジトリ構造・依存ルール・命名規則・層境界 | 静的コード構造 |
| `infra/provisioning/cue/` | OpenTofu出力値の型・契約検証 | 実行時インフラ値 |

**分離原則**: 両者は完全独立。`provisioning/cue` は `policy/cue` をimportしない。

### ストレージ方針（0.11.1継承・0.11.3強化）

| 用途 | 使用先 | 禁止 |
|-----|--------|------|
| 本番ストレージ | R2 | S3 |
| CI/開発 | MinIO (R2互換) | S3 |
| Tofu state backend | R2 (CI/本番) | S3 |
| 開発 state | ローカル (state/) | - |

**方針**: S3は将来的な復活も許可しない。R2が唯一のクラウドストレージ/バックエンド。

### 公式ワークフロー（0.11.3新規）

インフラ構成変更の標準手順：

```bash
# 1. Nix環境に入る
cd infra/provisioning/
nix develop

# 2. Plan実行（開発はローカルstate、CI/本番はR2バックエンド）
./scripts/plan.sh <環境名>

# 3. Apply実行
./scripts/apply.sh <環境名>

# 4. Output検証 + .env生成
./scripts/verify.sh <環境名>  # CUE検証
./scripts/export-env.sh <環境名>  # 検証済み値を.envに書き出し
```

**セキュリティポリシー**:
- ✅ tofu output → CUE検証 → .env生成の順守
- ❌ 検証前の値を直接 .env に書き込むことは禁止

---

## 再配置マッピング（0.11.1 → 0.11.2 → 0.11.3）

### 0.11.2で実施（継承）

| 旧パス | 新パス | 操作 |
|-------|--------|------|
| `infra/sdk/ui-wc/x-deck/` | `infra/presentation-runtime/x-deck/` | `git mv` |
| `infra/sdk/md-tools/md2html/` | `infra/content-build-tools/md2html/` | `git mv` |
| `infra/sdk/md-tools/mmd2svg/` | `infra/content-build-tools/mmd2svg/` | `git mv` |
| `infra/sdk/md-tools/pdf-export/` | `infra/content-build-tools/pdf-export/` | `git mv` |
| （新規） | `infra/content-build-tools/shared/` | 新規作成 |
| `interfaces/cli-docs/` | `interfaces/docs-build-cli/` | `git mv` |
| `interfaces/web-docs-vanilla/` | `interfaces/docs-static-site/` | `git mv` |

### 0.11.3で追加

| 項目 | 操作 |
|-----|------|
| `infra/provisioning/` | 新規作成（modules/environments/cue/scripts等） |
| `ci/workflows/infra-deploy.yml` | 新規追加 |
| `policy/cue/schemas/deps.cue` | `provisioning` を許可リストに追加 |

---

## 更新履歴

- **2025-10-25**: ADR 0.11.8適用、Manifest責務定義 & Capabilityガバナンス方針（docsのみ）
- **2025-10-25**: ADR 0.11.7適用、DoD整合性確認の完了（CUEガバナンス）
- **2025-10-25**: ADR 0.11.6適用、Finalize Secrets/Guard/IaC/Zoning policies
- **2025-10-25**: ADR 0.11.5適用、Secrets=唯一入口(手動) / CUE=SSOT / leaf分割 / Guard方針
- **2025-10-24**: ADR 0.11.4適用、sops-nix / flake細粒度 / manifest guard / Terranix→OpenTofu（R2）
- **2025-10-24**: ADR 0.11.3適用、最終形（0.11.2 + IaC統合）
- **2025-10-23**: ADR 0.11.2適用、命名統一・infra/sdk解体・dist責務固定
- **Supersedes**: ADR 0.11.2 → ADR 0.11.1（ストレージ方針）→ ADR 0.11.0（4層構造）→ ADR 0.10.12（Orchestration v4.1b）

---

**この文書が現行の正（SSOT）であり、過去のADRは履歴用として参照のみ。**

**生成方法**: 手動更新（将来的に `tools/generator` で自動生成予定）
