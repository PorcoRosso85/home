# Scheme - 型定義生成フレームワーク

このプロジェクトは、JSONスキーマベースの型定義生成システムを提供します。TypeScriptのインターフェース、クラス、型エイリアスからJSONスキーマを生成し、それらを再利用可能な形で管理します。

## プロジェクト構造

```
/home/nixos/scheme/
├── data/                          # データファイル格納ディレクトリ
│   ├── config/                    # 設定ファイル
│   │   ├── <Type>.<Meta>.config.json  # 型ごとの設定ファイル
│   │   └── ...
│   ├── generated/                 # 生成されたスキーマ
│   │   ├── <Type>.<Meta>.schema.json  # 生成されたスキーマファイル
│   │   └── ...
│   ├── meta/                      # メタスキーマ定義
│   │   ├── Function.meta.json     # 関数型メタスキーマ
│   │   ├── String.meta.json       # 文字列型メタスキーマ
│   │   └── Struct.meta.json       # 構造体型メタスキーマ
│   └── requirements/              # 統一要件定義
│       ├── <Type>.require.json    # 型ごとの統一要件ファイル
│       └── ...
├── src/                           # ソースコード
│   ├── application/               # アプリケーション層
│   │   ├── command.ts            # コマンドインターフェース
│   │   ├── depsCommand.ts        # 依存関係表示コマンド
│   │   ├── diagnoseCommand.ts    # 診断コマンド
│   │   ├── generateCommand.ts    # スキーマ生成コマンド
│   │   ├── listCommand.ts        # 一覧表示コマンド
│   │   ├── metaSchemaRegistryService.ts # メタスキーマ登録サービス
│   │   ├── registerCommand.ts    # メタスキーマ登録コマンド
│   │   ├── requirementsDepsUsecase.ts   # 要件間の依存関係解析ユースケース
│   │   ├── requirementsToFunctionUsecase.ts # 要件から関数定義への変換ユースケース
│   │   ├── validateCommand.ts    # バリデーションコマンド
│   │   └── validateConfigCommand.ts # 設定ファイルバリデーションコマンド
│   ├── domain/                    # ドメイン層
│   │   ├── config.ts             # 設定型定義
│   │   ├── generationService.ts  # スキーマ生成サービス
│   │   ├── metaSchema.ts         # メタスキーマ型定義
│   │   ├── metaSchemaRepository.ts # メタスキーマリポジトリ
│   │   ├── schema.ts             # スキーマ型定義
│   │   ├── service/              # ドメインサービス
│   │   │   ├── typeDependencyAnalyzer.ts # 型依存関係解析
│   │   │   └── typeDependencyService.ts  # 型依存関係サービス
│   │   └── validationService.ts  # バリデーションサービス
│   ├── infrastructure/            # インフラストラクチャ層
│   │   ├── fileMetaSchemaRepository.ts # ファイルベースメタスキーマリポジトリ
│   │   ├── fileSystemReader.ts   # ファイルシステム読み込み
│   │   └── fileSystemWriter.ts   # ファイル書き込み
│   ├── interface/                 # インターフェース層
│   │   ├── cli.ts                # CLI定義
│   │   ├── cliController.ts      # CLIコントローラ
│   │   ├── displayHelper.ts      # 表示ヘルパー
│   │   ├── requirements-generator.ts      # 要件生成インターフェース
│   │   └── generate-types-from-requirements.ts # 要件からの型生成インターフェース
│   └── service/                   # サービス層（非推奨 - アプリケーション層かドメイン層へ移行予定）
├── demo/                          # デモ・サンプル
│   ├── demo.generate.ts           # デモ生成スクリプト
│   └── run_deps_test.ts           # 依存関係テストスクリプト
├── doc/                           # ドキュメント
│   ├── CONVENTION.md             # 規約
│   ├── REQUIREMENTS-MANAGEMENT.md # 要件管理
│   └── SHEBANG-RULE.md           # シェバン規則
├── archive/                       # アーカイブ済み古いファイル
└── README.md                      # このファイル
```

## アーキテクチャと主要コンポーネント

## レイヤー構造

プロジェクトは下記のレイヤー構造を持っています：

1. **インターフェース層 (`interface/`)** - ユーザーとシステムの境界
   - CLIインターフェース
   - Web APIインターフェース(将来拡張用)

2. **アプリケーション層 (`application/`)** - ユースケースと実行制御
   - コマンドパターンを実装したコマンドクラス
   - ユースケースクラス(ファイル名にUsecaseサフィックス)

3. **ドメイン層 (`domain/`)** - ビジネスロジックとドメインモデル
   - 実際のビジネスロジックを実装したサービスクラス
   - ドメインモデルを表すインターフェースやクラス

4. **インフラストラクチャ層 (`infrastructure/`)** - 外部システムとのブリッジ
   - ファイルシステムやデータベースへのアクセスを実装

## 主要コンポーネントと役割

### コアコンポーネント

1. **メタスキーマ (`data/meta/`)**
   - システムで使用される型の定義を提供
   - `String.meta.json` - 文字列型の定義
   - `Struct.meta.json` - 構造体/オブジェクト型の定義
   - `Function.meta.json` - 関数型の定義

2. **スキーマ生成パイプライン**
   - **統一要件定義** - 型の要件を定義する
   - **スキーマ生成** - 統一要件ファイルからスキーマを生成

3. **ドメインモデル (`src/domain/`)**
   - システムの中核となる概念とロジックを定義
   - `schema.ts` - スキーマのインターフェース
   - `metaSchema.ts` - メタスキーマのインターフェース
   - `config.ts` - 設定のインターフェース

4. **アプリケーションサービス (`src/application/`)**
   - ユースケースを実装
   - `generateCommand.ts` - スキーマ生成コマンド
   - `validateCommand.ts` - バリデーションコマンド
   - `registerCommand.ts` - メタスキーマ登録コマンド

5. **インフラストラクチャ (`src/infrastructure/`)**
   - 外部とのデータやりとりを担当
   - `fileSystemReader.ts` - ファイル読み込み
   - `fileSystemWriter.ts` - ファイル書き込み

## 型生成ワークフロー

1. **統一要件JSONを作成**
   ```bash
   # 正しい使用方法
   ./src/interface/cli.ts req-gen create Schema --title="スキーマインターフェース" --desc="スキーマを表すインターフェース" --type=struct
   ```

2. **統一要件JSONを編集**
   - `data/requirements/Schema.require.json` を必要に応じて編集
   - 型のプロパティや制約を定義

3. **統一要件からスキーマを生成**
   ```bash
   # 正しい使用方法
   ./src/interface/cli.ts generate-types
   ```

4. **生成されたスキーマを確認**
   - `data/generated/Schema.Struct.schema.json`

## 依存関係とフロー

- **型の依存関係解析:**
  - `typeDependencyAnalyzer.ts` は型の依存関係を再帰的に解析
  - 自己参照や循環参照を適切に処理

## 命名規則

プロジェクト全体で以下の命名規則を採用しています：

### ファイル命名

- **ユースケースファイル**: `xxxUsecase.ts` 形式
  - 例: `requirementsDepsUsecase.ts`, `requirementsToFunctionUsecase.ts`
  - ユースケースレイヤーは application 層に統合され、ファイル名に `Usecase` サフィックスを付ける
  
- **コマンドファイル**: `xxxCommand.ts` 形式
  - 例: `generateCommand.ts`, `validateCommand.ts`
  - コマンドパターンを実装するクラスを含むファイル

- **サービスファイル**: `xxxService.ts` 形式
  - 例: `generationService.ts`, `validationService.ts`
  - 主要なビジネスロジックを実装するサービスを含むファイル

### クラス命名

- **インターフェース**: プレフィックスなし
  - 例: `Command`, `ValidationResult`

- **実装クラス**: `名前Impl` 形式
  - 例: `ValidationServiceImpl`, `GenerationServiceImpl`
  - インターフェースを実装するクラスには `Impl` サフィックスを付ける

### 変数/プロパティ命名

- **変数名**: キャメルケース
  - 例: `fileReader`, `metaSchemaId`

- **定数**: 大文字とアンダースコア
  - 例: `META_SCHEMA_DIR`, `REQUIREMENT_META_SCHEMA_PATH`


- **コマンドフロー:**
  - CLI要求 → `cli.ts` → 適切なコマンドクラス → ドメインサービス → インフラストラクチャ → ファイルシステム

- **生成フロー:**
  - 設定ファイル → `GenerationService` → スキーマ生成 → `FileSystemWriter` → 生成されたスキーマファイル

## コマンド一覧

`cli.ts` から利用可能なコマンドの一覧です：

| コマンド | 説明 | 使用例 |
|---------|-------|-------|
| `register` | メタスキーマを登録 | `./src/interface/cli.ts register ./data/meta/String.meta.json` |
| `generate` | スキーマを生成 | `./src/interface/cli.ts generate String ./data/config/Email.String.config.json ./data/generated/Email.String.schema.json` |
| `validate` | スキーマを検証 | `./src/interface/cli.ts validate ./data/generated/User.Struct.schema.json` |
| `diagnose` | メタスキーマや設定ファイルを診断 | `./src/interface/cli.ts diagnose meta ./data/meta/String.meta.json` |
| `list` | 登録済みのメタスキーマ一覧を表示 | `./src/interface/cli.ts list` |
| `deps` | 型の依存関係を再帰的に表示 | `./src/interface/cli.ts deps User.Struct` |
| `req-deps` | 要件間の依存関係を解析 | `./src/interface/cli.ts req-deps deps UserAuthentication` |
| `req-to-function` | 要件から関数定義JSONを生成 | `./src/interface/cli.ts req-to-function UserAuthentication` |
| `req-gen` | 統一要件JSONの生成と管理 | `./src/interface/cli.ts req-gen create NewFeature --title="新機能" --desc="新機能の説明" --type=function` |
| `generate-types` | 統一要件から型スキーマを一括生成 | `./src/interface/cli.ts generate-types` |

コマンドの詳細なヘルプを表示するには、引数なしでコマンドを実行します：

```bash
./src/interface/cli.ts
```

## 統一要件管理コマンド

統一要件の管理には `req-gen` コマンドを使用します：

| サブコマンド | 説明 | 使用例 |
|---------|-------|-------|
| `create` | 新しい統一要件を作成 | `./src/interface/cli.ts req-gen create NewFeature --title="新機能" --desc="新機能の説明" --type=function` |
| `convert` | 既存の要件を統一要件形式に変換 | `./src/interface/cli.ts req-gen convert ExistingFeature` |
| `list` | 統一要件一覧を表示 | `./src/interface/cli.ts req-gen list` |
| `validate` | 統一要件を検証 | `./src/interface/cli.ts req-gen validate UserAuthentication` |

## 主要なインターフェースとクラス

### インターフェース

- `Schema` - スキーマの基本構造を定義
- `MetaSchema` - メタスキーマの基本構造を定義
- `ValidationResult` - バリデーション結果を表現
- `TypeDependency` - 型の依存関係を表現
- `Command` - コマンドパターンの基本インターフェース

### クラス

- `FileSystemReader` - ファイルシステムからの読み込み
- `FileSystemWriter` - ファイルシステムへの書き込み
- `GenerationServiceImpl` - スキーマ生成ロジック
- `ValidationServiceImpl` - バリデーションロジック
- `MetaSchemaRegistryService` - メタスキーマの管理

## 拡張ポイント

このシステムを拡張するための主なポイント:

1. **新しいメタスキーマの追加**
   - `data/meta/` に新しいメタスキーマJSONを追加
   - `generationService.ts` に対応する生成ロジックを追加

2. **新しい型の追加**
   - `cli.ts req-gen` を使って要件を生成
   - 要件ファイルを編集
   - `cli.ts generate-types` を使ってスキーマを生成

3. **新しいコマンドの追加**
   - `Command` インターフェースを実装
   - `cli.ts` に新しいコマンドを登録

## 今後の改善点

1. **自動型抽出**
   - TypeScriptのソースコードから自動的に型定義を抽出
   - 抽出した型から要件JSONを自動生成

2. **設定ファイル自動生成**
   - 要件JSONから設定ファイルを自動生成するツール
   - 型の依存関係を自動的に解決

3. **スキーマの可視化**
   - 生成されたスキーマの依存関係を視覚的に表示
   - 型の関係性を理解しやすくする

4. **バリデーション機能の強化**
   - より詳細なエラーメッセージ
   - インタラクティブな修正支援

## Features ▲▲▲ New! ▲▲▲

### 統一要件スキーマ

要件管理と実装情報を統合した新しいスキーマにより、以下が可能になりました：

1. **要件と型の連携管理**
   - 要件JSONファイルと型定義の連携を柔軟に管理可能
   - 1ファイルに複数型の定義もサポート

2. **要件管理と実装情報の一元管理**
   - 要件の管理情報（ステータス、優先度など）と実装詳細を同一ファイルで管理可能
   - 情報の不整合を防止できる

3. **ディレクトリ構造のシンプル化**
   - requirements.generated/ ディレクトリの段階的な絶了が可能
   - ファイル管理、ディレクトリ構造がシンプルに

4. **統一要件管理機能**
   - 新規統一要件の作成が可能
   - 既存要件の統一要件形式への変換が可能
   - 要件の検証機能でエラーを早期発見可能
   - 統一要件一覧の表示が可能

5. **ワークフローの改善**
   - ステップ数の削減により開発効率が向上
   - 要件からスキーマ生成までのプロセスがシンプルに

### スキーマURI参照方式 ▲▲▲ New! ▲▲▲

スキーマの相互参照方式が新しくなりました：

1. **URIベースの参照方式**
   - 旧形式: `"$ref": "./data/generated/User.Struct.schema.json"`
   - 新形式: `"$ref": "scheme://User/local:Struct"`
   - ディレクトリ構造やファイル名への依存が解消され、より堅牙に

2. **メタスキーマソースの選択制**
   - 形式: `scheme://<型名>/<メタソース>:<メタスキーマ名>`
   - メタソースタイプ:
     - `local`: ローカルファイルシステム上のスキーマを参照
     - `web`: ウェブ上のスキーマを参照
     - `cdn`: CDN上のスキーマを参照
     - `opfs`: ブラウザのOrigin Private File System上のスキーマを参照

3. **引用統一性の向上**
   - 型名とメタスキーマ名による論理的な参照
   - 物理的なファイルパスに依存しない染み分け

4. **外部化への対応**
   - 将来的にメタスキーマをプロジェクトから切り離し、CDNやブラウザストレージに配置する準備
   - ソース切り替え時の影響範囲が限定的

### 環境変数と定数の中央管理 ▲▲▲ New! ▲▲▲

システム全体で使用される環境変数や定数を中央管理する仕組みが導入されました：

1. **variables.tsによる一元管理**
   - `/src/infrastructure/variables.ts` が全ての設定値を管理
   - ディレクトリパス、定数値、列挙型などが中央化

2. **環境変数による設定**
   - 以下の環境変数でカスタマイズ可能:
     - `SCHEME_BASE_DIR`: 基本ディレクトリ
     - `SCHEME_DATA_DIR`: データディレクトリ
     - `SCHEME_GENERATED_DIR`: 生成されたスキーマの保存先
     - `SCHEME_REQUIREMENTS_DIR`: 統一要件の保存先
     - `SCHEME_META_DIR`: メタスキーマの保存先
     - `SCHEME_WEB_BASE_URL`: WebソースのベースURL
     - `SCHEME_CDN_BASE_URL`: CDNソースのベースURL
     - `SCHEME_OPFS_BASE_PATH`: OPFSソースのベースパス
   
3. **特徴と利点**
   - 一貫性の向上: 値が一箇所で管理されるため、整合性が確保される
   - 保守性の向上: 変更が必要な場合、一箇所を修正するだけ
   - 染み分けの柔軟性: 環境ごとに異なる設定を適用可能

4. **使用例**

```typescript
// 使用例: variables.tsからのインポート

import { DIRECTORIES, META_SOURCE_TYPE, SCHEMA_CONFIG } from '../infrastructure/variables.ts';

// ディレクトリパスの使用
const schemaPath = `${DIRECTORIES.GENERATED}/${typeName}.${metaSchema}.schema.json`;

// メタソースタイプの使用
const uri = `${SCHEMA_CONFIG.URI_SCHEME}${typeName}/${META_SOURCE_TYPE.LOCAL}:${metaId}`;
```

### メタソースの切り替えコマンド

この新しい参照形式を使用するためのコマンドも利用可能です：

```bash
# ディレクトリ内のすべてのスキーマファイルの$refを新形式に変換
./src/interface/cli.ts convert-refs --dir=./data/generated

# 特定ファイルのみ変換
./src/interface/cli.ts convert-refs ./data/generated/User.Struct.schema.json
```
