# CozoDB Time Travel 実装プロジェクトTODO

## ✅ 実装ガイド作成
- ✅ CozoDB Time Travelの実装方法に関する包括的なガイドを作成する (`time_travel_guide.md`)
- ✅ サンプルコードと実装パターンを提供する (`cozoTimeTravelPattern.ts`)
- ✅ 異なるバージョンのエンティティを扱う方法を説明する

## Time Travel APIラッパー作成 ✅
- CozoDBのTime Travel機能をより簡単に利用できるAPIラッパーを作成する
- タイムスタンプの自動管理機能を提供する
- クエリ生成を自動化する関数を実装する
- 作業ステップ:
  1. `cozoTimeTravelApi.ts`ファイルの作成
  2. 高レベルAPIラッパー関数の設計と実装
  3. タイムスタンプ管理機能の実装
  4. クエリ生成の自動化機能の実装
  5. テスト関数とサンプルコードの作成
  6. ドキュメントの更新
- まだ動作確認ができていない
- NodeによるAPIでいいか？要検討

## 追加機能の実装
- バッチ操作のサポートを追加する
- スキーマ管理機能を強化する
- パフォーマンス最適化を行う
- 作業ステップ:
  1. バッチ操作用の関数設計
  2. 効率的なスキーマ定義と管理のパターン作成
  3. 大量データ処理のためのパフォーマンス最適化
  4. キャッシング機能の検討と実装
  5. テストケースの作成と性能計測

## ドキュメント整備
- 詳細なAPIドキュメントを作成する
- 使用例とベストプラクティスを提供する
- チュートリアルを作成する
- 作業ステップ:
  1. 各関数の詳細な使用方法ドキュメントの作成
  2. 一般的なユースケースとサンプルコードの提供
  3. ステップバイステップのチュートリアル作成
  4. エラー処理とトラブルシューティングガイドの追加
  5. パフォーマンスに関するベストプラクティスの整理

# Cozoによるスキーマ設計と関数型スキーマ同士の依存関係読み取り スキーマ依存関係管理システム - TODO

## 背景と概要

### meta.jsonとは

`meta.json`（実際には`/home/nixos/scheme/new/functional_programming/Function__Meta.json`へのシンボリックリンク）は、関数メタデータのスキーマ定義です。このスキーマに基づいて、多くの機能スキーマファイル（`*__Function.json`）が生成されています。これらのスキーマファイル間には依存関係が存在します。

### 目的

meta.jsonから生成される多くのスキーマファイルを1つのノードとしたときに、それらの依存関係をCozoDBで管理することが本プロジェクトの目的です。CozoDBは関係データベースとグラフデータベースの特性を持つデータベースシステムで、このような依存関係を効率的に管理できます。

### 対象とする依存関係

スキーマファイル内の`$ref`属性によって表現される依存関係を追跡します。具体的には以下の2種類を優先的に管理します：

1. 外部依存関係: `externalDependencies[].ref`
2. シグネチャの型依存関係:
   - パラメータ型: `properties.signatures.items.properties.parameterTypes.properties.$ref`
   - 戻り値型: `properties.signatures.items.properties.returnTypes.properties.$ref`

## アーキテクチャと実装計画

プロジェクトはクリーンアーキテクチャの原則に従い、以下の4つの層で構成します：

### 1. インフラストラクチャ層 (Infrastructure Layer)

**責務**: CozoDBとの通信、クエリの実行、データの永続化

**ディレクトリ**: `/infrastructure/schemaDependency/`

**主要ファイル**:
- `repository.ts`: CozoDBとの通信を担当するリポジトリ実装
- `queryBuilder.ts`: CozoDBクエリを構築するユーティリティ

**実装ステップ**:
1. CozoDBとの接続管理
2. 以下のリレーション定義の実装:
   ```sql
   // スキーマメタデータを保存するリレーション
   :create schema_meta {
     name: String,  // スキーマ名（ファイル名からの派生）
     type: String,  // スキーマのタイプ（例: "Function"）
     path: String,  // スキーマファイルのパス
     =>
     name
   }

   // スキーマ間の依存関係を保存するリレーション
   :create schema_dependency {
     source: String,            // 依存元スキーマ名
     target: String,            // 依存先スキーマ名
     refType: String,           // 参照タイプ（例: "external", "parameter", "return"）
     refPath: String,           // 参照パス
     =>
     source, target
   }
   ```
3. データ操作クエリの実装（登録、検索、削除）

### 2. ドメイン層 (Domain Layer)

**責務**: ビジネスロジック、依存関係解析、ドメインモデルの定義

**ディレクトリ**: `/domain/schemaDependency/`

**主要ファイル**:
- `model.ts`: スキーマと依存関係のドメインモデル
- `analyzer.ts`: $ref属性を検出して依存関係を解析するサービス
- `service.ts`: 依存関係管理の中核ビジネスロジック

**実装ステップ**:
1. ドメインモデルの定義（スキーマ、依存関係）
2. 依存関係解析ロジックの実装:
   - JSONファイルの読み込み
   - 指定されたパスパターンに基づいて$ref属性を検索
   - 見つかった$refから依存関係情報を抽出
3. 依存関係の種類（external、parameter、return）の特定

### 3. アプリケーション層 (Application Layer)

**責務**: ユースケース実装、ドメインサービスとインフラの連携

**ディレクトリ**: `/application/schemaDependency/`

**主要ファイル**:
- `schemaRegistryService.ts`: スキーマ登録と依存関係管理のユースケース
- `dependencyQueryService.ts`: 依存関係検索のユースケース

**実装ステップ**:
1. スキーマ登録ユースケースの実装
2. 依存関係検索ユースケースの実装
3. 依存関係グラフ構築ユースケースの実装
4. レポート生成ユースケースの実装

### 4. インターフェース層 (Interface Layer)

**責務**: CLI/APIインターフェース、入力バリデーション

**ディレクトリ**: `/interface/schemaDependency/`

**主要ファイル**:
- `cli.ts`: コマンドラインインターフェース
- `api.ts`: プログラム的に利用するためのAPI

**実装ステップ**:
1. CLIコマンドの定義（スキーマ登録、依存関係検索）
2. 入力バリデーションの実装
3. 出力フォーマットの定義（JSON、テキスト、Mermaid）

## 具体的な実装手順

### ステップ1: ドメインモデルとインフラストラクチャの実装

1. ドメインモデルの定義 (`domain/schemaDependency/model.ts`)
   ```typescript
   /**
    * スキーマメタデータを表すインターフェース
    */
   export interface SchemaMetadata {
     /** スキーマの名前 */
     name: string;
     /** スキーマのタイプ（function, class, interfaceなど） */
     type: string;
     /** スキーマファイルのパス */
     path: string;
   }

   /**
    * 依存関係タイプの列挙型
    */
   export enum DependencyType {
     /** 外部依存関係 */
     EXTERNAL = "external",
     /** パラメータ型依存関係 */
     PARAMETER = "parameter",
     /** 戻り値型依存関係 */
     RETURN = "return"
   }

   /**
    * 依存関係情報を表すインターフェース
    */
   export interface DependencyInfo {
     /** 依存元スキーマ名 */
     source: string;
     /** 依存先スキーマ名 */
     target: string;
     /** 依存関係の種類 */
     type: DependencyType;
     /** スキーマ内での参照パス */
     path: string;
   }
   ```

2. リポジトリインターフェースの定義 (`domain/schemaDependency/repository.ts`)
   ```typescript
   import { SchemaMetadata, DependencyInfo } from "./model";

   /**
    * スキーマリポジトリインターフェース
    */
   export interface SchemaRepository {
     /** リレーションを初期化する */
     initialize(): Promise<void>;
     
     /** スキーマメタデータを保存する */
     saveSchema(schema: SchemaMetadata): Promise<void>;
     
     /** 依存関係情報を保存する */
     saveDependency(dependency: DependencyInfo): Promise<void>;
     
     /** 指定されたスキーマの依存先を検索する */
     findDependencies(schemaName: string): Promise<DependencyInfo[]>;
     
     /** 指定されたスキーマに依存しているスキーマを検索する */
     findDependents(schemaName: string): Promise<DependencyInfo[]>;
   }
   ```

3. リポジトリ実装 (`infrastructure/schemaDependency/repository.ts`)
   ```typescript
   import { CozoDb } from "cozo-node";
   import { SchemaRepository } from "../../domain/schemaDependency/repository";
   import { SchemaMetadata, DependencyInfo } from "../../domain/schemaDependency/model";

   /**
    * CozoDBを使用したスキーマリポジトリの実装
    */
   export class CozoSchemaRepository implements SchemaRepository {
     private db: CozoDb;
     
     constructor() {
       this.db = new CozoDb();
     }
     
     async initialize(): Promise<void> {
       // リレーション作成クエリの実行
       // ...
     }
     
     async saveSchema(schema: SchemaMetadata): Promise<void> {
       // スキーマ保存クエリの実行
       // ...
     }
     
     // 以下、インターフェースの実装
     // ...
   }
   ```

### ステップ2: ドメインサービスの実装

1. 依存関係解析サービス (`domain/schemaDependency/analyzer.ts`)
   ```typescript
   import { DependencyInfo, DependencyType } from "./model";

   /**
    * 解析対象のパスパターン設定
    */
   export interface AnalyzerConfig {
     /** 外部依存関係のパスパターン */
     externalDependencyPaths: string[];
     /** パラメータ型依存関係のパスパターン */
     parameterTypePaths: string[];
     /** 戻り値型依存関係のパスパターン */
     returnTypePaths: string[];
   }

   /**
    * スキーマの依存関係を解析するサービス
    */
   export class DependencyAnalyzer {
     private config: AnalyzerConfig;
     
     constructor(config: AnalyzerConfig) {
       this.config = config;
     }
     
     /**
      * JSONスキーマから依存関係を解析する
      * @param schemaData スキーマデータ
      * @param schemaName スキーマ名
      * @returns 検出された依存関係情報の配列
      */
     analyze(schemaData: any, schemaName: string): DependencyInfo[] {
       const dependencies: DependencyInfo[] = [];
       
       // 外部依存関係の検出
       // ...
       
       // パラメータ型依存関係の検出
       // ...
       
       // 戻り値型依存関係の検出
       // ...
       
       return dependencies;
     }
     
     // ヘルパーメソッド
     // ...
   }
   ```

2. ドメインサービス (`domain/schemaDependency/service.ts`)
   ```typescript
   import fs from "fs";
   import path from "path";
   import { SchemaMetadata, DependencyInfo } from "./model";
   import { DependencyAnalyzer } from "./analyzer";
   import { SchemaRepository } from "./repository";

   /**
    * スキーマ依存関係管理のドメインサービス
    */
   export class SchemaDependencyService {
     private analyzer: DependencyAnalyzer;
     private repository: SchemaRepository;
     
     constructor(analyzer: DependencyAnalyzer, repository: SchemaRepository) {
       this.analyzer = analyzer;
       this.repository = repository;
     }
     
     /**
      * スキーマファイルを解析して依存関係を登録する
      * @param filePath スキーマファイルのパス
      */
     async processSchemaFile(filePath: string): Promise<void> {
       // ファイル読み込み
       // ...
       
       // メタデータ抽出
       // ...
       
       // 依存関係解析
       // ...
       
       // リポジトリへの保存
       // ...
     }
     
     // その他のビジネスロジック
     // ...
   }
   ```

### ステップ3: アプリケーション層の実装

1. スキーマ登録サービス (`application/schemaDependency/schemaRegistryService.ts`)
   ```typescript
   import { SchemaDependencyService } from "../../domain/schemaDependency/service";
   
   /**
    * スキーマ登録のユースケース
    */
   export class SchemaRegistryService {
     private dependencyService: SchemaDependencyService;
     
     constructor(dependencyService: SchemaDependencyService) {
       this.dependencyService = dependencyService;
     }
     
     /**
      * 単一のスキーマファイルを登録する
      * @param filePath スキーマファイルのパス
      */
     async registerSchemaFile(filePath: string): Promise<void> {
       try {
         await this.dependencyService.processSchemaFile(filePath);
       } catch (error) {
         // エラー変換と処理
         throw new Error(`スキーマファイルの登録に失敗しました: ${error.message}`);
       }
     }
     
     /**
      * ディレクトリ内の全スキーマファイルを登録する
      * @param dirPath ディレクトリパス
      * @param pattern ファイルパターン（例: "*.json"）
      */
     async registerSchemaDirectory(dirPath: string, pattern: string): Promise<void> {
       // ディレクトリ内のファイル検索と処理
       // ...
     }
   }
   ```

2. 依存関係クエリサービス (`application/schemaDependency/dependencyQueryService.ts`)
   ```typescript
   import { SchemaRepository } from "../../domain/schemaDependency/repository";
   import { DependencyInfo } from "../../domain/schemaDependency/model";
   
   /**
    * 依存関係検索のユースケース
    */
   export class DependencyQueryService {
     private repository: SchemaRepository;
     
     constructor(repository: SchemaRepository) {
       this.repository = repository;
     }
     
     /**
      * 指定されたスキーマが依存しているスキーマを検索
      * @param schemaName スキーマ名
      */
     async findDependencies(schemaName: string): Promise<DependencyInfo[]> {
       try {
         return await this.repository.findDependencies(schemaName);
       } catch (error) {
         // エラー変換と処理
         throw new Error(`依存関係の検索に失敗しました: ${error.message}`);
       }
     }
     
     /**
      * 指定されたスキーマに依存しているスキーマを検索
      * @param schemaName スキーマ名
      */
     async findDependents(schemaName: string): Promise<DependencyInfo[]> {
       // ...
     }
     
     /**
      * 依存関係グラフをMermaid形式で出力
      */
     async generateMermaidGraph(): Promise<string> {
       // ...
     }
   }
   ```

### ステップ4: インターフェース層の実装

1. CLIインターフェース (`interface/schemaDependency/cli.ts`)
   ```typescript
   #!/usr/bin/env -S nix shell nixpkgs#nodejs_22 --command node --experimental-strip-types
   
   import { program } from "commander";
   import { SchemaRegistryService } from "../../application/schemaDependency/schemaRegistryService";
   import { DependencyQueryService } from "../../application/schemaDependency/dependencyQueryService";
   
   // 依存関係の注入（実際の実装ではDIコンテナを使用するとよい）
   // ...
   
   // コマンド定義
   program
     .name("schema-dependency")
     .description("メタスキーマの依存関係を管理するツール");
   
   program
     .command("register")
     .description("スキーマを登録し、依存関係を解析する")
     .argument("<file-path>", "スキーマファイルのパス")
     .action(async (filePath) => {
       try {
         // スキーマ登録処理
         // ...
         console.log(`スキーマ ${filePath} を登録しました`);
       } catch (error) {
         console.error(`エラー: ${error.message}`);
         process.exit(1);
       }
     });
   
   // その他のコマンド
   // ...
   
   program.parse(process.argv);
   ```

## テスト計画

各層ごとに対応するテストを実装します。

1. **ドメイン層のテスト**
   - `test/domain/schemaDependency/analyzer.test.ts`: 依存関係解析のテスト
   - `test/domain/schemaDependency/service.test.ts`: ドメインサービスのテスト

2. **インフラストラクチャ層のテスト**
   - `test/infrastructure/schemaDependency/repository.test.ts`: リポジトリのテスト

3. **アプリケーション層のテスト**
   - `test/application/schemaDependency/schemaRegistryService.test.ts`: スキーマ登録のテスト
   - `test/application/schemaDependency/dependencyQueryService.test.ts`: 依存関係検索のテスト

4. **インターフェース層のテスト**
   - `test/interface/schemaDependency/cli.test.ts`: CLIのテスト

5. **統合テスト**
   - `test/integration/schemaDependency.test.ts`: 全層を通した統合テスト

## テスト用サンプルファイル

`samples/sample_with_dependencies.json`ファイルを使用して実装をテストします。このファイルには以下のタイプの依存関係が含まれています：

1. 外部依存関係（UserAuth、UserRegister）
2. シグネチャのパラメータ型依存関係（UserData）
3. シグネチャの戻り値型依存関係（AuthResult）

## 変更予定ファイル

| ファイルパス | 変更前概要 | 変更後概要 |
|--------------|------------|------------|
| `/home/nixos/scheme/new/cozo/domain/schemaDependency/model.ts` | （新規ファイル） | スキーマと依存関係のドメインモデル定義。SchemaMetadata、DependencyType、DependencyInfoインターフェースを提供。 |
| `/home/nixos/scheme/new/cozo/domain/schemaDependency/repository.ts` | （新規ファイル） | リポジトリインターフェース定義。SchemaRepositoryインターフェースでCozoDBとのやり取りを抽象化。 |
| `/home/nixos/scheme/new/cozo/domain/schemaDependency/analyzer.ts` | （新規ファイル） | 依存関係解析のドメインサービス。スキーマから$ref属性を検出して依存関係を抽出。 |
| `/home/nixos/scheme/new/cozo/domain/schemaDependency/service.ts` | （新規ファイル） | 依存関係管理のドメインサービス。スキーマの処理と依存関係登録のビジネスロジック。 |
| `/home/nixos/scheme/new/cozo/infrastructure/schemaDependency/repository.ts` | （新規ファイル） | CozoDBを使用したリポジトリ実装。SchemaRepositoryインターフェースを実装し、CozoDBとの通信を担当。 |
| `/home/nixos/scheme/new/cozo/infrastructure/schemaDependency/queryBuilder.ts` | （新規ファイル） | CozoDBクエリ構築ユーティリティ。複雑なクエリを構築するヘルパー関数を提供。 |
| `/home/nixos/scheme/new/cozo/application/schemaDependency/schemaRegistryService.ts` | （新規ファイル） | スキーマ登録のユースケース実装。スキーマファイルの登録とエラー処理を担当。 |
| `/home/nixos/scheme/new/cozo/application/schemaDependency/dependencyQueryService.ts` | （新規ファイル） | 依存関係検索のユースケース実装。依存関係の検索と結果の整形を担当。 |
| `/home/nixos/scheme/new/cozo/interface/schemaDependency/cli.ts` | （新規ファイル） | コマンドラインインターフェース。ユーザーとのやり取りとアプリケーション層の呼び出しを担当。 |
| `/home/nixos/scheme/new/cozo/interface/schemaDependency/api.ts` | （新規ファイル） | プログラム的に利用するためのAPI。外部からのアクセスポイントを提供。 |
| `/home/nixos/scheme/new/cozo/samples/sample_with_dependencies.json` | （新規ファイル） | 外部依存関係とシグネチャ型依存関係を含むサンプルスキーマ。テスト用データとして使用。 |

## 注意点と考慮事項

1. **メタスキーマの変更への対応**
   - 解析対象の$refパスパターンは`AnalyzerConfig`で設定可能にする
   - 新しいパスパターンを追加できるよう拡張性を持たせる

2. **疎結合設計**
   - 依存方向は外側から内側へ（インターフェース層 → アプリケーション層 → ドメイン層 → インフラストラクチャ層）
   - インターフェースを通じた依存性の注入により、実装の詳細を隠蔽
   - 既存の`dependencyAnalyzer.ts`には依存しない

3. **エラー処理**
   - インフラ層のエラーはドメイン層で適切なドメインエラーに変換
   - アプリケーション層でユーザー向けエラーメッセージを生成
   - デバッグ情報とユーザー向けメッセージを区別

4. **ドキュメント**
   - すべてのクラスとメソッドにJSDocコメントを追加
   - 複雑なロジックには説明コメントを付与
   - README.mdを作成し、使用方法を説明
