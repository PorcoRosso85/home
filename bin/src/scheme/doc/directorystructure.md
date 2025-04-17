# スキーマシステムディレクトリ構成

このドキュメントでは、スキーマシステムのディレクトリ構成について説明します。

## 全体構成

```
/home/nixos/scheme/
├── data/                         # 全データを格納するディレクトリ
│   ├── generated/                # 生成されたスキーマファイル
│   ├── config/                   # 設定ファイル
│   ├── meta/                     # メタスキーマ
│   ├── requirements/             # 統一要件定義ファイル
│   └── tmp/                      # 一時ファイル（生成プロセス用）
├── doc/                          # ドキュメント
│   ├── reference/                # リファレンスドキュメント
│   ├── namingconvention.md       # 命名規則ドキュメント
│   └── directorystructure.md     # ディレクトリ構成ドキュメント
├── src/                          # ソースコード
│   ├── interface/                # インターフェース層
│   ├── application/              # アプリケーション層
│   │   ├── xxxCommand.ts         # コマンドクラス
│   │   └── xxxUsecase.ts         # ユースケースクラス
│   ├── domain/                   # ドメイン層
│   │   └── service/              # ドメインサービス
│   ├── infrastructure/           # インフラストラクチャ層
│   └── service/                  # その他のサービス（ユーティリティ）
├── demo/                         # デモ・サンプル
└── archive/                      # アーカイブ済み古いファイル
```

## ディレクトリの役割

### data ディレクトリ

メインのデータディレクトリで、すべてのスキーマ関連ファイルを格納します。

#### generated サブディレクトリ

生成されたスキーマファイルを保存します。これらのスキーマはグラフ情報としてフロントエンドで使用され、プロジェクト設計情報として活用されます。型ごとのサブディレクトリは使用せず、すべてのスキーマファイルは直接このディレクトリに配置されます。

- 命名規則: `<概念名>.<Type>.schema.json`
- 例: `Email.String.schema.json`

#### config サブディレクトリ

スキーマ生成のための設定ファイルを保存します。これらは生成プロセスのソースとして保持されます。将来的にJSON以外の形式を生成する可能性も考慮しています。型ごとのサブディレクトリは使用せず、すべての設定ファイルは直接このディレクトリに配置されます。

- 命名規則: `<概念名>.<Type>.config.json`
- 例: `Email.String.config.json`

#### meta サブディレクトリ

各型のメタスキーマを保存します。メタスキーマはスキーマ生成の基盤となるものです。

- 命名規則: `<Type>.meta.json`
- 例: `String.meta.json`

#### requirements サブディレクトリ

統一要件定義ファイルを保存します。各要件ファイルは、要件情報と実装詳細を一元管理します。

- 命名規則: `<概念名>.require.json`
- 例: `UserAuthentication.require.json`

#### tmp サブディレクトリ

生成プロセス中に必要な一時ファイルを保存します。長期保存は想定していません。

- 命名規則: `<概念名>.<Type>.tmp.<タイムスタンプ>.json`
- 例: `Email.String.tmp.20250321.json`

### src ディレクトリ

システムのソースコードを格納します。クリーンアーキテクチャに基づいて以下のレイヤーで構成されています：

#### interface サブディレクトリ

ユーザーインターフェース層で、CLIやWeb APIなどのインターフェースを提供します。この層はユーザーと直接やり取りし、入力の検証や出力のフォーマット変換を担当します。

- 主要ファイル:
  - `cli.ts`: CLIの基本機能
  - `cliController.ts`: コマンド振り分けと実行制御
  - `requirements-generator.ts`: 要件生成インターフェース
  - `generate-types-from-requirements.ts`: 要件からの型生成インターフェース

#### application サブディレクトリ

アプリケーション層で、ユースケースを実装し、業務フローを制御します。この層では下位レイヤー（ドメイン層）のサービスを調整します。

- 主要ファイル:
  - `xxxCommand.ts`: コマンドパターンを実装したコマンドクラス
  - `xxxUsecase.ts`: 特定のユースケースを実装したクラス
  - `metaSchemaRegistryService.ts`: メタスキーマ登録サービス

#### domain サブディレクトリ

ドメイン層で、ビジネスロジックとドメインモデルを定義します。このレイヤーはプロジェクトの核心部分を形成します。

- 主要ファイル:
  - `schema.ts`: スキーマのインターフェース
  - `metaSchema.ts`: メタスキーマのインターフェース
  - `generationService.ts`: スキーマ生成サービス
  - `validationService.ts`: バリデーションサービス
  - `service/typeDependencyAnalyzer.ts`: 型依存関係解析

#### infrastructure サブディレクトリ

インフラストラクチャ層で、外部システムとの連携を担当します。ファイルシステムやデータベースとの通信を実装します。

- 主要ファイル:
  - `fileMetaSchemaRepository.ts`: ファイルベースのメタスキーマリポジトリ
  - `fileSystemReader.ts`: ファイルシステム読み込み
  - `fileSystemWriter.ts`: ファイル書き込み

### demo ディレクトリ

システムのデモやサンプルスクリプトを格納します。システムの基本的な使用例を提供します。

- 主要ファイル:
  - `demo.generate.ts`: サンプル型のスキーマ生成デモ
  - `run_deps_test.ts`: 依存関係テストスクリプト

### doc ディレクトリ

システムに関する各種ドキュメントを格納します。

- `reference/`: 各型のリファレンスドキュメント
- `namingconvention.md`: 命名規則の詳細
- `directorystructure.md`: このドキュメント
- `CONVENTION.md`: コーディング規約
- `MIGRATION.md`: 移行手順書
- `REQUIREMENTS-MANAGEMENT.md`: 要件管理の説明
