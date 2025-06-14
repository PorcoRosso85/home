# コーディング規約と開発ルール

## 開発の基本原則

### 1. Parse, don't validate
- データ検証ではなくデータパースを優先する
  - バリデーションでエラーを出すのではなく、パースで適切な型に変換する
  - 入力データは常に「未検証の生データ」として扱い、ドメインオブジェクトへの変換を確実に行う
  - 変換できない場合は早期に失敗し、不正な値が内部に伝播しないようにする
  - 型システムを駆使して、コンパイル時に不正な状態を防ぐ

### 2. 純粋なドメイン層とアプリケーション層
- domainとapplicationレイヤーは完全に外部影響から分離する
  - これらの層では純粋関数のみを使用し、副作用を排除する
  - 外部との通信やファイルI/O、データベースアクセスなどを排除する
  - 状態変更は新しい値を返すことで表現する（不変性の原則）
  - ドメインモデルは自己完結し、どの環境でも同じ結果を返す

### 3. 外部との境界処理
- interface/infrastructureレイヤーでのみ外部影響・副作用を扱う
  - 外部データをドメインオブジェクトに変換する責務を負う
  - ドメインオブジェクトを外部形式に変換する責務を負う
  - すべての例外処理とエラーハンドリングを行う
  - 入出力のバリデーションではなく、パースによる変換を行う

### 4. 既存ファイルの確認
- 新しいファイルを作成する前に、同名または同様の機能を持つファイルが既に存在するか確認すること
- 既存ファイルを上書きする場合は必ずバックアップを取ること

### 5. コードレビューと改善提案
- 既存のファイルやコードに不足箇所や改善点がある場合は、ユーザーに改善を提案すること
- 提案は具体的な改善方法と、その理由を明示すること

### 6. リファクタリングのルール
- リファクタリングを行う際は、機能を変更せず、コードの品質と可読性の向上に集中すること
- 大規模な変更の前にはユーザーの承認を得ること

## レイヤー構造と責任分担

### ディレクトリ構造
- クリーンアーキテクチャの原則に従い、以下の層に分けること
  - `interface`: UIとユーザー入力の処理、外部との境界層
  - `application`: ユースケースとアプリケーションサービス、純粋な関数で実装
  - `domain`: ドメインモデルとビジネスルール、副作用なしの純粋な関数で実装
  - `infrastructure`: 外部システムとの連携、副作用を含む処理の実装

### ドメインレイヤー
- 純粋な関数による実装を徹底する
- 副作用を含まないビジネスロジックの設計
- 外部依存を持たず、他のレイヤーからも影響を受けない
- 型定義と純粋なビジネスロジックのみを含む

### アプリケーションレイヤー
- ユースケースの実装を担当
- ドメインロジックを組み合わせて機能を実現
- 外部依存を直接持たず、型で表現された依存のみを許可
- 副作用を含まない純粋関数スタイルを基本とする

### インターフェース/インフラストラクチャレイヤー
- 外部影響・副作用を扱う唯一のレイヤー
- 外部APIとの通信処理
- データベースアクセス
- ファイルシステム操作
- 外部サービスとの連携
- 境界での厳格な型変換処理

## コーディング規約

### 1. 型定義の使用方針

#### type定義のみを使用し、interfaceは使わない

```typescript
// 推奨: type定義のみを使用
type NodeType = {
  id: string;
  name: string;
  description?: string;
};

// 非推奨: interfaceの使用
// interface INode {
//   id: string;
//   name: string;
//   description?: string;
// }
```

#### 型安全性の強化

```typescript
// プリミティブ型をラップしたドメイン特有の型
type NodeId = string & { readonly _brand: unique symbol };

// スマートコンストラクタ関数（値オブジェクトの生成）
function createNodeId(value: string): NodeId | InvalidNodeIdError {
  if (!value || value.length < 3) {
    return {
      type: 'InvalidNodeIdError',
      message: 'Node ID must be at least 3 characters long'
    };
  }
  return value as NodeId;
}
```

#### ノミナル型を活用してより厳密な型安全性を確保する

```typescript
// 構造的部分型ではなくノミナル型の使用例
type UserId = { readonly _tag: 'UserId'; value: string };
type ProductId = { readonly _tag: 'ProductId'; value: string };

// これにより文字列が同じでもUserIdとProductIdは別物として扱われる
function parseUserId(id: string): UserId | Error {
  if (!id.startsWith('user_')) {
    return new Error('Invalid user ID format');
  }
  return { _tag: 'UserId', value: id };
}
```

### 2. エラー処理

#### 例外ではなく値としてのエラー

```typescript
// エラー型の定義
type NodeNotFoundError = {
  type: 'NodeNotFoundError';
  message: string;
  nodeId: string;
};

type InvalidNodeError = {
  type: 'InvalidNodeError';
  message: string;
  details: string[];
};

// 複数のエラー型を共用型で組み合わせる
type NodeError = NodeNotFoundError | InvalidNodeError;

// 関数の戻り値型として成功とエラーの両方を表現
type GetNodeResult = NodeType | NodeError;

// 関数の実装例
function getNode(id: string): GetNodeResult {
  // 条件に応じてエラーまたは成功値を返す
  if (!nodeExists(id)) {
    return {
      type: 'NodeNotFoundError',
      message: `Node with ID ${id} not found`,
      nodeId: id
    };
  }
  
  // 成功時の値を返す
  return {
    id,
    name: `Node ${id}`,
    description: 'A node description'
  };
}

// 型によるエラーハンドリング
function handleGetNodeResult(result: GetNodeResult): void {
  // 型の判別（Type Narrowing）
  if ('type' in result) {
    // エラーケース
    console.error(`Error: ${result.message}`);
    
    // 型によるエラー分岐
    if (result.type === 'NodeNotFoundError') {
      // 特定のエラーに対する処理
      console.error(`Node ID: ${result.nodeId}`);
    } else if (result.type === 'InvalidNodeError') {
      // 別のエラーに対する処理
      console.error(`Details: ${result.details.join(', ')}`);
    }
  } else {
    // 成功ケース
    console.log(`Node: ${result.name}`);
  }
}
```

#### Either型の活用（オプション）

```typescript
type Either<E, A> = { tag: 'left'; left: E } | { tag: 'right'; right: A };

function left<E, A>(e: E): Either<E, A> {
  return { tag: 'left', left: e };
}

function right<E, A>(a: A): Either<E, A> {
  return { tag: 'right', right: a };
}

function parseAge(age: unknown): Either<string, number> {
  if (typeof age !== 'number') {
    return left('Age must be a number');
  }
  if (age < 0) {
    return left('Age must be positive');
  }
  return right(age);
}
```

#### エラーをフォールバック処理で隠蔽しない

エラーを隠す一切の行為（フォールバックやデフォルト値設定）は禁止します。エラーは常に明示的に処理され、呼び出し元に伝播する必要があります。

```typescript
// 非推奨: エラーをフォールバックで隠す
function getNodeUnsafe(id: string): NodeType {
  try {
    // 何らかの処理
    if (!nodeExists(id)) {
      // エラーをフォールバックで隠蔽
      return {
        id: 'default',
        name: 'Default Node',
        description: 'This is a fallback node'
      };
    }
    return fetchNode(id);
  } catch (error) {
    // エラーを隠蔽して空のデータを返す
    return {
      id: 'error',
      name: 'Error Node',
      description: 'An error occurred'
    };
  }
}

// 推奨: エラーを明示的に伝播する
function getNodeSafe(id: string): NodeType | NodeError {
  if (!nodeExists(id)) {
    return {
      type: 'NodeNotFoundError',
      message: `Node with ID ${id} not found`,
      nodeId: id
    };
  }
  
  try {
    return fetchNode(id);
  } catch (error) {
    return {
      type: 'NodeFetchError',
      message: 'Failed to fetch node',
      details: error instanceof Error ? error.message : String(error)
    };
  }
}
```

### 3. Parse, don't validateの実装

#### 検証ではなく変換

```typescript
// 非推奨: バリデーションのみを行うアプローチ
// function validateNodeData(data: unknown): boolean {
//   if (typeof data !== 'object' || data === null) return false;
//   const node = data as any;
//   return typeof node.id === 'string' && typeof node.name === 'string';
// }

// 推奨: パースによるデータ変換のアプローチ
type RawNodeData = unknown;

function parseNodeData(data: RawNodeData): NodeType | InvalidNodeError {
  // 型チェック
  if (typeof data !== 'object' || data === null) {
    return {
      type: 'InvalidNodeError',
      message: 'Invalid node data: not an object',
      details: ['Expected object, got ' + typeof data]
    };
  }

  const rawNode = data as Record<string, unknown>;
  
  // ID の検証と変換
  if (typeof rawNode.id !== 'string' || rawNode.id.length === 0) {
    return {
      type: 'InvalidNodeError',
      message: 'Invalid node data: missing or invalid id',
      details: ['id must be a non-empty string']
    };
  }

  // 名前の検証と変換
  if (typeof rawNode.name !== 'string' || rawNode.name.length === 0) {
    return {
      type: 'InvalidNodeError',
      message: 'Invalid node data: missing or invalid name',
      details: ['name must be a non-empty string']
    };
  }

  // オプションフィールドの処理
  const description = typeof rawNode.description === 'string' 
    ? rawNode.description 
    : undefined;

  // 安全なドメインオブジェクトを返す
  return {
    id: rawNode.id,
    name: rawNode.name,
    description
  };
}
```

#### スマートコンストラクタパターン

```typescript
// 悪い例（バリデーション型）
function validateEmail(email: string): boolean {
  return email.includes('@');
}

// 良い例（パース型）
type Email = { value: string };

function parseEmail(raw: string): Email | Error {
  if (!raw.includes('@')) {
    return new Error('Invalid email format');
  }
  return { value: raw };
}
```

#### 型駆動設計

```typescript
// 悪い例
type User = {
  age: number; // 負の値も許容してしまう
}

// 良い例
type PositiveInteger = { value: number };

function parsePositiveInteger(n: number): PositiveInteger | Error {
  if (n <= 0 || !Number.isInteger(n)) {
    return new Error('Not a positive integer');
  }
  return { value: n };
}

type User = {
  age: PositiveInteger;
}
```

### 4. 非同期処理のパターン

#### Promiseを使った非同期関数のエラーハンドリング

```typescript
// 非同期関数の返り値型
type AsyncGetNodeResult = Promise<NodeType | NodeError>;

// 非同期関数の実装例
async function getNodeAsync(id: string): AsyncGetNodeResult {
  try {
    const response = await fetchNodeData(id);
    return parseNodeData(response);
  } catch (error) {
    // 外部エラーを適切なドメインエラーに変換
    return {
      type: 'NodeNotFoundError',
      message: `Failed to fetch node with ID ${id}`,
      nodeId: id
    };
  }
}

// 非同期関数の使用例
async function handleNodeOperation(id: string): Promise<void> {
  const result = await getNodeAsync(id);
  
  if ('type' in result) {
    // エラー処理
    console.error(`Error: ${result.message}`);
  } else {
    // 成功処理
    console.log(`Node: ${result.name}`);
  }
}
```

### 5. レイヤー間のコミュニケーション

#### 公開APIとプライベート関数

```typescript
// ドメインレイヤーの公開API
export type Node = {
  id: string;
  name: string;
  description?: string;
};

export type NodeError = NodeNotFoundError | InvalidNodeError;

export function parseNode(data: unknown): Node | NodeError {
  // 実装...
}

// プライベート関数（非公開）
function validateNodeId(id: string): boolean {
  // 実装...
}
```

#### アダプター パターン

```typescript
// インフラストラクチャレイヤーのアダプター
type NodeRepositoryAdapter = {
  getNode: (id: string) => Promise<Node | NodeError>;
  saveNode: (node: Node) => Promise<Node | NodeError>;
  // 他のメソッド...
};

// アプリケーションレイヤーでの使用
function createGetNodeUseCase(repository: NodeRepositoryAdapter) {
  return async function(id: string): Promise<Node | NodeError> {
    return await repository.getNode(id);
  };
}
```

### 6. 関数型プログラミングアプローチ

#### クラス使用の制限
- 状態保存をしない場合は可能な限りクラスを使用せず、純粋な関数として実装すること
- 必要な状態がある場合のみクラスを使用し、責務を明確にすること
- 関数型プログラミングのアプローチを優先し、副作用を最小限に抑えること
- 新しいクラスの作成は必要最小限にとどめ、既存のクラスは可能な限り関数に変換すること

#### 関数型プログラミングの原則
- 純粋関数（副作用のない関数）を優先的に使用
- 状態の変更よりも新しい値を返す関数を使用
- 不変性（immutability）を重視
- 関数合成を活用して複雑な処理を構築

#### 関数と変数の命名規則
- 関数名は動詞または動詞+名詞の形式を使用（例: `createNode`, `parseSchema`）
- パース関数は必ず`parse`プレフィックスを使用（例: `parseEmail`, `parseUserId`）
- 略語を避け、完全な単語を使用
- キャメルケース（camelCase）を使用
- 変数名は意味のある名前を使用し、短すぎる変数名（例: `a`, `x`）を避ける
- `util`および`utils`という命名を避ける（具体的な機能を表す名前を使用すること）
  - 悪い例: `utils.ts`, `fileUtils.ts`
  - 良い例: `formatter.ts`, `fileOperations.ts`, `stringManipulation.ts`

### 7. ファイル命名規則
- TypeScriptファイルにはキャメルケースを使用すること（例: `metaSchemaRepository.ts`）
- クラス名やインターフェース名にはパスカルケースを使用すること（例: `MetaSchemaRepository`）
- メタスキーマファイルは `.meta.json` で終わること
- 設定ファイルは `.config.json` で終わること
- 生成されたスキーマは `.schema.json` で終わること

### 8. 型システムの活用

#### 型チェック
- すべてのファイルは `--check` フラグを使用して厳格な型チェックを行う
- **`--no-check` フラグの使用は禁止**
- 型エラーは無視せず、必ず修正する
- 型定義が不明確な場合は、明示的な型アノテーションを追加する
- 型チェックを回避するための `any` 型の使用は最小限に抑える
- 型の安全性を確保するために、必要に応じて型ガードやアサーションを使用する

### 9. コード改善例

#### 改善前: インフラへの直接依存とtry/catchの使用

```typescript
// 改善前の実装例（参考）
class NodeRepository {
  private graphDataService: GraphDataService;
  private logger: Logger;

  constructor() {
    this.graphDataService = new GraphDataService();
    this.logger = new Logger();
  }

  async getNode(id: string) {
    try {
      return await this.graphDataService.getNode(id);
    } catch (error) {
      this.logger.error(`ノード取得エラー (ID: ${id})`, error);
      throw error;
    }
  }
}
```

#### 改善後: 外部依存の分離とエラーを値として扱う

```typescript
// 改善後の実装例
type NodeRepository = {
  getNode: (id: string) => Promise<NodeType | NodeError>;
};

type NodeRepositoryDependencies = {
  fetchNode: (id: string) => Promise<unknown>;
};

function createNodeRepository(deps: NodeRepositoryDependencies): NodeRepository {
  return {
    getNode: async (id: string) => {
      try {
        const rawData = await deps.fetchNode(id);
        return parseNodeData(rawData);
      } catch (error) {
        return {
          type: 'NodeNotFoundError',
          message: `Failed to fetch node with ID ${id}`,
          nodeId: id
        };
      }
    }
  };
}

// インフラストラクチャレイヤーでの使用例
const nodeRepository = createNodeRepository({
  fetchNode: async (id) => {
    // 実際のデータ取得ロジック
    const graphDataService = new GraphDataService();
    const result = await graphDataService.getNode(id);
    return result;
  }
});
```

## テスト方針

### 1. In-Source テスト
- 単体テストはテストファイルを作成せず、実装ファイル内に直接記述する
- すべてのファイルは、そのファイル自身をテストする機能を含むべき
- ファイル実行時にテストが自動的に実行されるよう設定する
- テストコードはファイル末尾に配置し、明確なコメントで区切る
- `import.meta.main`を使用して直接実行された場合のみテストを実行する
- 特別なテストモードフラグやオプションを使用せず、単純な実行でテスト可能にする

### 2. テスト独立性
- 単体テストは別ファイルでのテストや外部ファイルに依存したテストは禁止
- 各モジュールは自己完結したテストを含める
- 外部依存を必要とする場合はモックを使用

### 3. レイヤーの分離を考慮したテスト
- ドメイン層とアプリケーション層は外部依存なしでテスト可能であることを確認
- インターフェース層とインフラストラクチャ層のテストでは境界の変換処理に焦点を当てる
- ドメインオブジェクトと外部表現の変換が正しく行われることを確認

### 4. テスト実行方法
- In-Source テストの実行コマンド例:
  ```
  deno run --allow-read --allow-write path/to/file.ts
  ```
- または以下のshebangを使用したファイルの場合:
  ```
  ./path/to/file.ts
  ```

### 5. テスト追加のルール
- 新規作成またはバグ修正時には、最低1つの正常系テストケースを追加すること
- パース関数のテストには必ず正常系と異常系の両方のケースを含める
- 一つのテストは一つの機能の正常系動作を確認するものとする
- 複雑なエッジケースや大量のテストケースを含むテストスクリプトの作成は避ける
- 簡潔で理解しやすいテストケースを心がける
- テストケースは明確に定義され、期待される結果を明示
- 境界条件やエッジケースを含める
- 失敗ケースもテストする

### 6. E2Eテスト規約
- E2Eテストは単体テストと明確に分離し、専用の`/test`ディレクトリに配置
- E2Eテストファイル名はキャメルケース（例: `functionGraph.ts`, `schemaValidator.ts`）
- E2Eテストはプロジェクトルートから`deno run --allow-read --allow-write test/[テストファイル名].ts`で実行
- スクリプト内にはシバンを含める
- E2Eテストファイルは、プロジェクト内の複数モジュールを組み合わせたテストを目的とする
- 各ファイルは実行可能な独立したスクリプトとして機能する
- 単体テストとは異なり、外部ファイル（例：Function.meta.json）に依存してもよい
- テスト結果は標準出力に表示し、必要に応じてレポートファイルを生成
- 生成されたファイルは`.gitignore`に追加するか、一時ディレクトリに出力

## ドキュメント規約

### 1. 関数ドキュメント
- 各関数の目的と動作を説明
- パラメータと戻り値を文書化
- パース関数の場合は変換ルールとエラー条件を明記
- 例外やエッジケースについて記述

### 2. モジュールドキュメント
- ファイルの先頭にモジュールの説明を含める
- モジュールの役割と責任を明記
- 他のモジュールとの関係を説明

### 3. 型ドキュメント
- 複雑な型定義には説明を付ける
- 型の制約や意図を文書化
- ドメインルールを型コメントとして記載

## 実行環境

- スクリプトファイルは用途に応じて適切なshebangを使用する:
  - 標準的なCLIスクリプト:
    ```
    #!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write --allow-run --check
    ```
  - Web APIサーバースクリプト:
    ```
    #!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-net --allow-read --check
    ```
  - Deno直接実行スクリプト:
    ```
    #!/usr/bin/env -S nix run nixpkgs#deno -- run -A
    ```
- 実行権限が必要な場合は、開発者に明示的に申し出ること
- `--check`フラグは常に含めること（型チェックの重要性）
- 例外としてビルドスクリプトや変換ツールなど特殊な用途のスクリプトでは`-A`フラグを使用可能
- 新規作成するツールスクリプトは全て上記のshebangルールを守ること

## 特定のファイル・ディレクトリの取り扱い

### データディレクトリ
- `./data/config/` および `./data/meta/` の変更は慎重に行うこと
- これらのディレクトリのファイルを変更する場合は、事前にユーザーの許可を得ること
- 変更を行う場合は元の状態を復元できるようにしておくこと

### ドキュメントディレクトリ
- `./doc/` 内のドキュメントは常に最新の状態に保つこと
- コード変更によってドキュメントが古くなった場合は、ドキュメントも合わせて更新すること

## まとめ

- type定義のみを使用し、interface定義は使わない
- エラーは値として扱い、例外に依存しない
- Either型やResult型などの複雑なモナド型は使用を最小限にし、共用型（union type）でエラーを表現する
- 「Parse, don't validate」パターンを使用し、早期に安全な型に変換する
- レイヤー間の依存は型で表現し、実装は依存注入で差し替え可能にする
- ドメインとアプリケーションレイヤーは副作用を含まず、純粋な関数で実装する
- 型安全性を常に最優先し、型エラーは確実に修正する
- ファイル命名規則を厳守し、モジュールの役割を明確にする

## エラー表示とレンダリング規約

### 1. エラーレンダリングの基本原則

- エラーに関するレンダリングは一切禁止します
- エラーによりレンダリングできなかった場合は、何も表示せず（nullを返し）、標準ポップアップのみで対応します
- エラーは常にコンソールログに出力し、詳細情報を開発者向けに残します
- カスタムエラーUI（エラーボックス、エラーメッセージ、警告アイコンなど）の作成は禁止します

### 2. エラー表示とコンソールの整合性

- UIからエラーが表示されないようにする一方で、コンソールには正確な情報を出力します
- エラー発生時はコンポーネントのレンダリングをスキップし、親コンポーネントの処理に任せます
- エラー内容はコンソールで確認し、UIには一切表示しません

### 3. 実装例

```typescript
// 非推奨: エラー時に専用のUIを表示
const TreeNode: React.FC<TreeNodeProps> = ({ node }) => {
  if (!node.uri) {
    logger.warn('TreeNode: node.uri が未定義またはnullです', { nodeName: node.name });
    return (
      <div style={{ 
        backgroundColor: 'rgba(255, 0, 0, 0.1)', 
        padding: '10px', 
        margin: '5px 0',
        borderRadius: '4px',
        border: '1px solid red'
      }}>
        <p>エラー: URIが未設定のノード</p>
        <code>{JSON.stringify({ name: node.name })}</code>
      </div>
    );
  }
  
  // 正常なレンダリング処理...
}

// 推奨: エラー時には何も表示せず、ログのみ出力
const TreeNode: React.FC<TreeNodeProps> = ({ node }) => {
  if (!node.uri) {
    logger.warn('TreeNode: node.uri が未定義またはnullです', { nodeName: node.name });
    // 何も表示しない
    return null;
  }
  
  // 正常なレンダリング処理...
}
```

### 4. RFC URIによるノードID設定

ノードIDは以下のURI形式に準拠する必要があります：

- `file:///path/to/resource.ts#symbolName` - ファイルパスとシンボル名
- `file:///path/to/resource.ts#class:ClassName` - クラス参照
- `file:///path/to/resource.ts#class:ClassName.method:methodName` - メソッド参照
- `http://example.com/path/to/resource#anchor` - Web URL参照

ノードのURIが正しいRFC形式でない場合はエラーとして扱い、レンダリングを行わないようにします。
