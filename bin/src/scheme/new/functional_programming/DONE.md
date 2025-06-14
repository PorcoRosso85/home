# Function.meta.json 改善計画, タスク

このドキュメントは、Function.meta.jsonスキーマの将来的な改善案をまとめたものです。

## コード規約作成（クラス使用の禁止と関数型アプローチの強制） ✅

以下のコード規約を新たに制定し、プロジェクト全体に適用します：

1. クラス宣言の禁止
   - 新しいクラスの作成は禁止
   - 既存のクラスは関数に変換する
   - TypeScriptのクラス構文の使用を避ける

2. 関数型プログラミングの原則の適用
   - 純粋関数（副作用のない関数）を優先的に使用
   - 状態の変更よりも新しい値を返す関数を使用
   - 不変性（immutability）を重視

3. 型定義の使用
   - interfaceよりもtype aliasを優先的に使用
   - 型の合成と再利用を促進
   - 型レベルプログラミングの活用

4. コードの構造化
   - モジュール化と関数の合成を促進
   - 小さな関数の組み合わせで複雑な処理を実現
   - 暗黙的な依存関係を避け、明示的な関数引数を使用

## 依存型と型レベルプログラミングの強化 ✅

以下のステップで依存型と型レベルプログラミングの機能を強化します：

1. ドメインモデルの拡張 ✅
   - domain/features/dependentTypes.ts の作成 ✅
   - TypeLevelProgrammingFeature インターフェースの定義 ✅
   - 依存型、シングルトン型、リファインメント型の詳細定義 ✅

2. 依存型のスキーマ生成機能を実装 ✅
   - application/schemas/dependentTypeSchema.ts の作成 ✅
   - 型レベル計算の表現機能の実装 ✅
   - 値から型への依存関係の表現機能 ✅

3. 型レベルプログラミングの実装 ✅
   - 型レベル関数の表現 ✅
   - 型レベルでの条件分岐と再帰の表現 ✅
   - 型レベルでの証明と検証機能 ✅

4. スキーマビルダーへの統合 ✅
   - 既存の型システム機能との統合 ✅
   - メタプログラミング機能の追加 ✅
   - 実行時型情報との連携 ✅

## リファクタリング: クラスの廃止と関数型アプローチへの移行 ✅

以下のステップでクラスを廃止し、一貫した関数型アプローチに移行します：

1. SchemaBuilderServiceImpl クラスの関数化 ✅
   - createBaseSchema メソッドを純粋関数として再実装
   - addPropertyToSchema メソッドを純粋関数として再実装
   - addRequiredProperty メソッドを純粋関数として再実装
   - generateCompleteSchema メソッドを純粋関数として再実装
   - シングルトンインスタンスの代わりに関数のエクスポート

2. interfaceの型定義への変換 ✅
   - SchemaBuilderService インターフェースを型定義に変換
   - メソッド定義を関数型の型定義に変換

3. 依存モジュールの更新 ✅
   - genSchema.ts の修正（クラスインスタンスではなく関数を使用）
   - スキーマ生成処理のパイプライン化と関数合成の促進

4. テストの更新 ✅
   - 動作テスト実行による確認

## 型システムの強化 ✅

以下のステップで型システムに関する詳細なメタデータを追加します：

1. ドメインモデルの拡張 ✅
   - domain/features/typeSystem.ts の作成
   - TypeSystemFeature インターフェースの定義
   - ADT、ジェネリック、依存型のサブ型の定義

2. スキーマ生成機能の実装 ✅
   - application/schemas/typeSystemSchema.ts の作成
   - createTypeSystemSchema 関数の実装
   - サブコンポーネント（ADT、ジェネリック等）の実装

3. スキーマビルダーへの統合 ✅
   - generateCompleteSchema 関数の拡張
   - typeSystem プロパティの追加と連携

4. 型システム機能の個別実装 ✅
   - 代数的データ型（ADT）のサポート
     - サム型とプロダクト型の表現
     - パターンマッチングのサポート情報
   - ジェネリック型のサポート
     - 型パラメータと制約の表現
     - 高階型の表現方法
   - 依存型のサポート
     - 値に依存した型の表現
     - 精緻な型制約の記述

## コンポジションに関する情報 ✅

- 「composition」セクションの追加 ✅
  - 関数合成の方法やパターンの記述 ✅
  - 合成可能性（composability）の特性 ✅
- 関数パイプラインの構成方法 ✅
  - データフロー図の表現 ✅
  - パイプライン最適化の可能性 ✅

## コード品質向上: --no-checkフラグの禁止 ✅

以下のステップでプロジェクト全体のコード品質を向上させます：

1. プロジェクト全体の見直し ✅
   - 型エラーの検出と修正 ✅
   - インポートパスの修正（.tsの拡張子追加など） ✅
   - 未使用のコードや冗長な記述の削除 ✅

2. 規約ファイルの更新 ✅
   - README.mdに型チェックの重要性について記述を追加 ✅
   - CONVENTION.mdに「--no-checkフラグの使用禁止」を明記 ✅
   - 型チェックエラーの修正方法に関するガイドラインを追加 ✅

3. CIパイプラインの更新 ✅
   - 型チェックを自動実行するステップを追加 ✅
   - 型エラーがあるコードのマージを防止する仕組みの導入 ✅

## ./new/functional_prgramming/functionsディレクトリの削除 ✅

- 動作テスト
- 問題なく削除できるか確認
- 削除実施
- 動作テスト

## テストを型情報として含める ✅

- テストが必要かどうかのフラグ情報 ✅
- テストケース生成ヒント ✅
  - エッジケースの識別 ✅
  - 境界条件の明示 ✅
  - 特に動作保証確認・仕様ドキュメントとして役割を果たす、必ず最低必要とする正常系テストケース一つ ✅
- プロパティベーステストの戦略 ✅
  - 生成すべき入力の性質 ✅
  - 不変条件の定義 ✅
- テスト容易性の評価基準 ✅
  - モック化可能性 ✅
  - 分離テスト戦略 ✅

## 実装済みスキーマ生成処理の応用 ✅

- 一部の生成処理をスキップする機能 ✅
  - 一定のケースで詳細すぎるプロパティを含まないスキーマを生成したい ✅

## 既存機能の整理 ✅

- all-propertiesをデフォルトとする ✅
- dry-run機能の確認＋必要に応じて削除 ✅
  - dry-run機能は正常に動作していることを確認したため、削除不要と判断

## 2020-12対応 ✅

- draft-07から移行

## 生成されるスキーマのモジュール化設計検討 ✅

- ~~いくつかのモジュールによりスキーマが構成されるようにすることを検討~~
  - ~~スキーマの責務分割~~
  - ~~責務の排他条件の整理簡易化を期待~~
- ~~ただスキーマ生成をプログラム化済み（メタプログラムがある状態）のため、その必要性の確認から行いたい~~

検討結果 (2025/03/31):
- 生成処理は関数型アプローチにより既に適切にモジュール化されている
- 各機能の生成処理は独立した純粋関数として実装されており、内部的なモジュール化は実現済み
- スキーマファイル自体のモジュール化（複数JSONファイルへの分割）は現時点では見送り
  - 理由: 既存コードベースで十分な分離が達成されている、物理的分割は複雑性を追加する可能性
- 将来、必要に応じて各モジュールが独立ファイルを生成し、それらを参照するスキーマを生成する戦略が有効
- 詳細は schemaBuilderServiceImpl.ts の generateCompleteSchema 関数コメントに記録

## 動的参照・動的スコープ導入の検討 ✅

※ このトピックは関数型プログラミングではなくjson schemaの策定に関するものである
- 導入したらどうなるか
- 導入する場合、プロパティの排他性考慮が必要
- 以下注意点
```log
JSON Schema における共通化は主に $ref や動的スコープ ($dynamicRef, $dynamicAnchor) で行われますが、ここでも過剰な共通化は問題を引き起こします。

過剰な $ref を避ける:

細かすぎる分割: あまりに小さな単位で $defs を作り $ref で参照しすぎると、スキーマの構造が細切れになり、全体像を把握するのが難しくなります。どこで何が定義されているか追うのが大変になります。

影響範囲の拡大: 広く使われる共通定義を安易に変更すると、意図しない多くの箇所に影響が出る可能性があります。

対策:

意味のある単位で共通化: 本当に複数の場所で「全く同じ」定義が必要な場合や、論理的にまとまった意味を持つ単位（例: address, user_profile など）で共通化します。

少しの違いなら別定義: 少しでも意味合いや制約が異なる場合は、無理に $ref で共通化せず、別の定義として作成するか、allOf などで基本定義に制約を追加する方が明確な場合があります。

動的スコープ ($dynamicRef) の慎重な利用:

動的スコープは強力ですが、多用するとスキーマの解決パスが複雑になり、どの定義が最終的に適用されるのかを理解・デバッグするのが非常に困難になります。

対策:

明確なパターンに限定: 再帰的な構造のノード定義をカスタマイズする場合など、動的スコープが明確なメリットをもたらす場合に限定して利用します。

アンカー名の明確化: $dynamicAnchor には、その役割が明確にわかる名前を付けます。

代替手段の検討: oneOf や if/then/else など、他のキーワードでよりシンプルに表現できないか検討します。

シンプルさと可読性を優先:

DRY は重要ですが、それ以上にスキーマの 読みやすさ、理解しやすさ、メンテナンスのしやすさ を優先します。場合によっては、多少の重複を許容する方が、結果的に良い設計になることもあります。

合成的なアプローチ (allOf, anyOf, oneOf):

既存のスキーマ定義を組み合わせて新しい定義を作ることで、再利用性を高めつつ、継承的な複雑さを避けることができます。例えば、ベースとなるスキーマ定義に allOf を使って追加の制約やプロパティを組み合わせるなど。

```

## 既存機能の整理 ✅

- all-properties? all-features? はデフォルト動作→削除 ✅

## 今回の実装アプリの、既存アプリケーションとの代替性 ✅

- 代替候補
  - MongoDB
  - Neo4j

## 過剰な設計でないか, json schema構造の見直し検討 ✅

- 関数型のスキーマとして拡張の手間を減らしたい→これが最初のスキーマサイズの増大につながっているがこれは適切か？
- json schemaを採用する理由は以下のとおり
  - すべてのプログラミングにおいてもほぼ標準ライブラリで対応される
  - ポータビリティが維持される
  - idなどのprimary keyだけでなく、プロパティの一部が他のjsonを参照することがある特性を活かせる -> RDBでない
  - 半構造性 -> RDBでない
  - json schema同士の連携状態を探索可能 -> GraphDBでないといけないことはない
- 運用上一つのメタスキーマから大量に生成されたスキーマファイルの更新について
  - 本生成器xから生成されるスキーマXをメタスキーマとするスキーマYが、Xに従っている証明を保持する
    - これにより、Xに従ったバリデーションの結果Yが機能するあるいは機能しないことをハンドリング可能とする

検討結果 (2025/03/31):
- スキーマサイズは40KBであり、関数型プログラミングの詳細な特性（代数的データ型、依存型、カリー化、純粋性など）を表現するためには、この程度の複雑さは適切である
- JSON Schemaの採用理由（ポータビリティ、標準ライブラリサポート、半構造性）は妥当であり、要件を満たしている
- 今後の改善案として、スキーマの主要コンポーネントをさらに整理し、オプショナルな拡張部分と必須部分を明確に分離するアプローチを検討するべき
- ユースケースに応じて簡略化されたスキーマを生成できる機能も考慮に値する

議事録 (2025/03/31): スキーマNullable化検討
---------------------------------------------
※ スキーマのオプショナル化ではなく、参照側でのNullable対応について検討

### Nullableにするべきケースと対象

1. **設計初期フェーズでの使用**
   - 実装詳細を決定する前の概念設計段階
   - 基本的な関数シグネチャと型の関係性のみを定義したい段階

2. **ドキュメント生成目的での使用**
   - APIドキュメントや関数カタログ作成が主目的
   - エンドユーザー向けの説明が必要な場合

3. **ライブラリ利用者視点での情報提供**
   - ライブラリを使用する開発者に必要な情報のみを提示
   - 内部実装の詳細は隠蔽したい場合

4. **パフォーマンス最適化が不要なケース**
   - 性能よりも機能性を重視する場合
   - プロトタイピングやPoC段階

5. **言語固有の機能を利用しないクロスプラットフォーム開発**
   - 複数言語での実装を前提とする場合
   - 特定言語の機能に依存しない共通定義が必要な場合

### Nullable対象となる項目

1. **実装詳細関連**
   - 評価戦略 (evaluation)
   - メモ化 (memoization)
   - スレッドセーフ性
   - 最適化情報

2. **高度な型システム機能**
   - 依存型の詳細情報
   - 型レベルプログラミング
   - 代数的データ型の詳細

3. **テスト関連情報**
   - テストケース生成ヒント
   - プロパティベーステスト戦略
   - テスト容易性の評価指標

4. **パフォーマンス特性**
   - 計算量の詳細
   - メモリ使用量
   - スケーラビリティ特性

5. **形式的検証と意味論**
   - 形式的仕様
   - 意味論の詳細
   - 検証手法

### Nullable（旧オプショナル）を採用する理由

スキーマを参照するJSON側での対応として、「Nullable（null可能）な形で全プロパティを参照しつつ、値がないことを明示するルール」という方針を採用することとした。理由は以下の通り：

1. **スキーマの一貫性維持**: スキーマ自体は常に完全な形で存在するため、参照側での解釈にぶれが生じにくい

2. **バージョン互換性の向上**: スキーマの各部分が常に存在することで、バージョン間の互換性が保ちやすくなる

3. **部分的採用の柔軟性**: 参照側のJSONが必要な部分だけを埋めることで、実質的に「オプショナル」な使い方ができる

4. **検証の容易さ**: 値が明示的に「null」であることと「未定義」であることを区別できるため、検証が容易になる

参照側JSONでの実装例：
```json
{
  "signature": "function add(a: number, b: number): number",
  "description": "Adds two numbers and returns the result",
  
  // 高度な情報は「使用しない」ことを明示
  "typeSystem": null,
  "performance": null,
  
  // または
  "typeSystem": { "used": false },
  "performance": { "used": false }
}
```

このアプローチにより、開発フェーズやユースケースに応じて、参照側JSONが必要な情報のみを含みつつも、スキーマとの整合性を保つことができる。

## 依存処理解析を優先実装 ✅

- ./src配下と./new配下、解析処理が重複している
- 関数型に関しては ./newに実装する
- またメタスキーマ生成関数が「どこに$refがあるか」を教えてくれるはず
  - 生成関数に$refを問い合わせられれば、$refが仕様上どこに追加・どこから削除されても、解析処理が仕様変更を追えることを期待
  - スキーマと解析処理が同期することを期待

### 依存処理解析実装 (2025/03/31) ✅

以下の内容を実装しました：

1. 関数型アプローチによる新実装
   - `domain/service/referenceAnalyzer.ts` - 参照解析の基本型と関数を実装
   - `domain/service/dependencyAnalyzer.ts` - 依存関係ツリーの構築と解析機能を実装
   - `application/refCollector.ts` - スキーマから$ref参照を収集するユーティリティ関数を実装

2. スキーマ生成との統合
   - `application/schemaBuilderServiceImpl.ts` - $ref収集機能を組み込み

3. インフラストラクチャ層の更新
   - `infrastructure/fileSystem.ts` - ファイル読み込みインターフェースの実装
   - `infrastructure/schemaFileRepository.ts` - 非同期処理対応のために更新

4. CLI定義の更新
   - `interface/depsCommand.ts` - 依存解析コマンドのハンドラーを実装
   - `cli.ts` - サブコマンド処理機能を追加

5. 確認・検証
   - スキーマ生成機能 (`./cli.ts --verbose`) が正常に動作することを確認
   - 依存解析コマンド (`./cli.ts deps`) が正常に動作することを確認
   - $refをサポートする主要プロパティとその解析が正しいことを確認

## グラフ構造への対応 ✅

ツリー形式はあくまで表示形式であり、ドメインエンティティとしてはエッジリスト形式のグラフ構造を基本とする実装に移行する必要があります。

### グラフ構造への対応計画 (2025/04/02) ✅

以下の作業を行い、依存関係をエッジリスト形式のグラフ構造として表現します：

#### 1. ドメインエンティティの型定義 ✅

1. `domain/entities/graph.ts` の作成
   - ノード型の定義（ID、ラベル、プロパティなど）
   - エッジ型の定義（ID、ソース、ターゲット、ラベル、プロパティなど）
   - グラフ構造の型定義（ノードとエッジのコレクション）

```typescript
// 実装例
export type Node = {
  id: string | number;
  labels: string[];
  properties: Record<string, unknown>;
};

export type Edge = {
  id: string | number;
  source: string | number;  // ソースノードID
  target: string | number;  // ターゲットノードID
  label: string;
  properties: Record<string, unknown>;
};

export type Graph = {
  nodes: Node[];
  edges: Edge[];
};
```

#### 2. 依存関係解析処理の拡張 ✅

1. `domain/service/graphBuilder.ts` の作成
   - 依存関係ツリーからグラフ構造へ変換する関数
   - スキーマからグラフ構造を直接構築する関数

```typescript
// 実装例
import { TypeDependency } from "./referenceAnalyzer.ts";
import { Graph, Node, Edge } from "../entities/graph.ts";

/**
 * 依存関係ツリーからグラフ構造へ変換する
 */
export function dependencyTreeToGraph(tree: TypeDependency): Graph {
  // 実装内容
}

/**
 * スキーマから依存関係グラフを直接構築する
 */
export function buildDependencyGraph(schema: unknown): Graph {
  // 実装内容
}
```

#### 3. グラフ構造のシリアライズと表示 ✅

1. `application/serializers/graphSerializer.ts` の作成
   - グラフ構造のJSON形式へのシリアライズ関数
   - GraphViz/DOT形式への変換関数
   - Mermaid形式への変換関数

```typescript
// 実装例
import { Graph } from "../../domain/entities/graph.ts";

/**
 * グラフをJSON形式にシリアライズする
 */
export function serializeToJson(graph: Graph): string {
  // 実装内容
}

/**
 * グラフをGraphViz/DOT形式に変換する
 */
export function convertToDot(graph: Graph): string {
  // 実装内容
}

/**
 * グラフをMermaid形式に変換する
 */
export function convertToMermaid(graph: Graph): string {
  // 実装内容
}
```

#### 4. CLI機能の拡張 ✅

1. `interface/depsCommand.ts` の拡張
   - グラフ出力形式の指定オプションの追加
   - 出力フォーマットの選択機能
   
```typescript
// 実装例 - オプション拡張
interface DepsCommandOptions {
  schemaPath: string;
  verbose: boolean;
  format: "tree" | "json" | "dot" | "mermaid";
  outputPath?: string;
}
```

#### 5. 既存実装の移行 ✅

1. 既存の依存関係表示関数をグラフベースに移行
   - `dependencyToString` → グラフからツリー形式の文字列を生成する関数に変更
   - `analyzeDependencies` → グラフ構造を基本として処理するよう変更

     // 実装内容
     // インデント付きの文字列を生成
   }
   ```

2. `/home/nixos/scheme/new/functional_programming/domain/service/dependencyAnalyzer.ts` - 依存関係解析の関数
   ```typescript
   import { SchemaReference, TypeDependency } from "./referenceAnalyzer.ts";
   import { FileReader } from "../../infrastructure/fileSystem.ts";

   /**
    * オブジェクト内の$ref属性を検索して依存関係を抽出する
    */
   export async function findReferences(
     obj: unknown,
     dependencies: TypeDependency[],
     fileReader: FileReader,
     schemaDir: string,
     visitedTypes: Set<string>
   ): Promise<void> {
     // 実装内容
     // オブジェクトを再帰的に探索し、$ref属性を検出して解析
   }

   /**
    * 型の依存関係を再帰的に取得する
    */
   export async function getDependencies(
     typeName: string,
     metaSchema: string,
     fileReader: FileReader,
     schemaDir: string = "./data/generated",
     visitedTypes: Set<string> = new Set<string>()
   ): Promise<TypeDependency> {
     // 実装内容
     // スキーマファイルを読み込み、依存関係を解析
   }
   ```

**アプリケーション層**:

3. `/home/nixos/scheme/new/functional_programming/application/commands/depsAnalyzer.ts` - 依存関係解析コマンド
   ```typescript
   import { FileReader } from "../../infrastructure/fileSystem.ts";
   import { getDependencies, dependencyToString } from "../../domain/service/dependencyAnalyzer.ts";

   /**
    * 型の依存関係を解析するコマンド処理
    */
   export async function analyzeDependencies(
     args: { typeName: string; metaSchema: string; debug?: boolean },
     fileReader: FileReader,
     schemaDir: string
   ): Promise<string> {
     // 実装内容
     // 依存関係を解析して結果を文字列で返す
   }
   ```

4. `/home/nixos/scheme/new/functional_programming/application/refCollector.ts` - スキーマ生成時の$ref収集機能
   ```typescript
   /**
    * スキーマ生成中に$ref属性を収集する
    */
   export function collectReferences(schema: unknown): string[] {
     // 実装内容
     // スキーマから$ref属性を収集して返す
   }
   ```

**インターフェース層**:

5. `/home/nixos/scheme/new/functional_programming/interface/depsCommand.ts` - CLI統合
   ```typescript
   import { analyzeDependencies } from "../application/commands/depsAnalyzer.ts";
   import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";

   /**
    * 依存関係解析のCLIコマンド処理
    */
   export async function handleDepsCommand(args: string[]): Promise<void> {
     // 実装内容
     // 引数を解析し、analyzeDependencies関数を呼び出して結果を表示
   }
   ```

#### 2. スキーマ生成との統合

1. スキーマビルダーサービスに$ref収集機能を組み込む
   ```typescript
   // application/schemaBuilderServiceImpl.ts に追加
   
   import { collectReferences } from "./refCollector.ts";
   
   /**
    * 生成されたスキーマから参照情報を収集する
    */
   export function getSchemaReferences(schema: FunctionSchema): string[] {
     return collectReferences(schema);
   }
   
   // schemaBuilderService オブジェクトに関数を追加
   export const schemaBuilderService = {
     // 既存の関数
     createBaseSchema,
     addPropertyToSchema,
     addRequiredProperty,
     generateCompleteSchema,
     
     // 新しい関数
     getSchemaReferences
   };
   ```

#### 3. インフラストラクチャ層の更新

1. `FileReader` インターフェースの実装
   ```typescript
   // infrastructure/fileSystem.ts
   
   /**
    * ファイル読み込みインターフェース
    */
   export interface FileReader {
     readFile(path: string): Promise<string>;
     readJsonFile(path: string): Promise<unknown>;
     exists(path: string): Promise<boolean>;
   }
   
   /**
    * Denoファイルシステム実装
    */
   export class DenoFileSystem implements FileReader {
     async readFile(path: string): Promise<string> {
       return await Deno.readTextFile(path);
     }
     
     async readJsonFile(path: string): Promise<unknown> {
       const text = await this.readFile(path);
       return JSON.parse(text);
     }
     
     async exists(path: string): Promise<boolean> {
       try {
         await Deno.stat(path);
         return true;
       } catch {
         return false;
       }
     }
   }
   ```

#### 4. CLI定義の更新

1. `cli.ts`に依存解析コマンドを追加
   ```typescript
   // cli.ts に追加

   import { handleDepsCommand } from "./interface/depsCommand.ts";

   // コマンドハンドラーの設定
   const commandHandlers: Record<string, (args: string[]) => Promise<void>> = {
     // 既存のコマンド
     // ...
     
     // 依存関係解析コマンド
     "deps": handleDepsCommand,
   };
   ```

### 機能対比表：既存実装と新実装

| 機能説明 | 既存実装パス | 新実装パス | 変更点 |
|---------|------------|-----------|-------|
| **参照解析と解決** | `src/domain/service/schemaReferenceResolver.ts` (クラス) | `new/functional_programming/domain/service/referenceAnalyzer.ts` (関数) | クラスベースから関数型アプローチへ変更 |
| **URIからの参照情報解析** | `SchemaReferenceResolver.parseReference()` (メソッド) | `parseReference()` (純粋関数) | クラスからの独立、純粋関数化 |
| **依存関係ツリーの再帰的取得** | `src/domain/service/typeDependencyAnalyzer.ts` の `getDependencies()` | `new/functional_programming/domain/service/dependencyAnalyzer.ts` の `getDependencies()` | 副作用を明示的に分離、型安全性向上 |
| **$ref属性の検索・抽出** | `typeDependencyAnalyzer.ts` の `findReferences()` | `dependencyAnalyzer.ts` の `findReferences()` | 再帰処理の最適化、型安全性向上 |
| **依存関係の文字列表現変換** | `typeDependencyAnalyzer.ts` の `dependencyToString()` | `referenceAnalyzer.ts` の `dependencyToString()` | 出力フォーマットの一貫性維持 |
| **依存関係表示コマンド** | `src/application/depsCommand.ts` (クラス) | `new/functional_programming/application/commands/depsAnalyzer.ts` (関数) | コマンドパターンからアプリケーションサービス関数へ |
| **ファイル読み込み処理** | `src/infrastructure/fileSystemReader.ts` (クラス) | `new/functional_programming/infrastructure/fileSystem.ts` (インターフェースと実装) | より明確なインターフェース定義、拡張性向上 |
| **コマンドライン統合** | `src/interface/cli/cliController.ts` の `deps` コマンド | `new/functional_programming/interface/depsCommand.ts` の `handleDepsCommand()` | 依存注入の明示化、関数型アプローチ |

### 新規追加機能

| 機能説明 | 新実装パス | 利点 |
|---------|-----------|------|
| **スキーマ生成時の$ref収集** | `new/functional_programming/application/refCollector.ts` の `collectReferences()` | スキーマ生成と同時に依存関係を把握可能 |
| **スキーマビルダー統合** | `new/functional_programming/application/schemaBuilderServiceImpl.ts` の `getSchemaReferences()` | 生成時に参照情報を取得可能、変更の同期が容易 |
| **型安全な参照情報モデル** | `new/functional_programming/domain/service/referenceAnalyzer.ts` の型定義 | タイプミスなどによるバグを防止、IDE補完サポート |
| **循環参照の改善検出** | `dependencyAnalyzer.ts` の `getDependencies()` | 関数型アプローチによる明示的な状態管理 |
| **ファイル存在チェック** | `fileSystem.ts` の `exists()` | ファイル操作の安全性向上 |

### 実装スケジュール

1. **第1フェーズ: インフラストラクチャ層** (完了予定: 2025/04/07)
   - FileReader インターフェースの実装
   - Denoファイルシステム実装クラスの作成
   - 単体テストの作成

2. **第2フェーズ: ドメイン層** (完了予定: 2025/04/14)
   - 参照解析機能の実装
   - 依存関係解析機能の実装
   - 単体テストの作成

3. **第3フェーズ: アプリケーション層** (完了予定: 2025/04/21)
   - 依存関係解析コマンドの実装
   - スキーマ生成時の$ref収集機能の実装
   - スキーマビルダーサービスとの統合

4. **第4フェーズ: インターフェース層** (完了予定: 2025/04/28)
   - CLI統合の実装
   - エンドツーエンドテストの作成

5. **第5フェーズ: 評価と最適化** (完了予定: 2025/05/05)
   - パフォーマンス評価
   - エラーハンドリングの強化
   - ドキュメント整備

### 既存実装の削除計画

1. **移行準備期間** (2025/05/05 - 2025/05/19)
   - 新実装の動作検証
   - 既存実装との互換性確認
   - 移行ドキュメントの作成

2. **移行推奨期間** (2025/05/19 - 2025/06/02)
   - 既存実装に廃止予定警告を追加
   - 新実装への移行を促す

3. **削除実行** (2025/06/02)
   - 既存の依存解析コードを完全に削除
   - 新実装のみを残す

