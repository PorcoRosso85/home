# TypeScript Language Server コード編集機能

## 主要なコード編集機能

### 1. Code Actions（コードアクション）
TypeScript LSPは以下のコードアクションをサポート：

- **`source.fixAll.ts`** - 自動修正可能な問題を一括修正
  - 到達不可能なコード
  - 非同期関数でないメソッドでのawait使用
  - インターフェースの不正確な実装

### 2. リファクタリング コマンド

#### a) Organize Imports（インポート整理）
```json
{
  "command": "_typescript.organizeImports",
  "arguments": [
    "file:///path/to/file.ts",
    { "skipDestructiveCodeActions": true }
  ]
}
```
- 未使用のインポートを削除
- インポートをアルファベット順にソート
- TypeScript 4.4以降で破壊的変更をスキップ可能

#### b) Apply Code Action（コードアクション適用）
```json
{
  "command": "_typescript.applyCodeAction",
  "arguments": [codeActionObject]
}
```
- 特定のリファクタリングを実行
- Extract Method（メソッド抽出）
- Extract Variable（変数抽出）
- Move to new file（新規ファイルへ移動）

#### c) Rename File（ファイル名変更）
```json
{
  "command": "_typescript.applyRenameFile",
  "arguments": [{
    "sourceUri": "file:///old/path.ts",
    "targetUri": "file:///new/path.ts"
  }]
}
```
- ファイル名変更時に全インポートを自動更新

#### d) Go to Source Definition
```json
{
  "command": "_typescript.goToSourceDefinition",
  "arguments": [documentUri, position]
}
```

### 3. 大規模リファクタリング対応

#### Rename（名前変更）
- **プロジェクト全体での一括変更**
- シンボル（変数、関数、クラス、インターフェース等）の名前変更
- 全ての参照箇所を自動的に更新

#### Workspace Edit（ワークスペース編集）
- 複数ファイルにまたがる変更を一括実行
- トランザクショナルな変更（全て成功するか全て失敗）

#### Code Action Resolution（2024年の進化）
- 大規模な編集操作を遅延実行
- 初回リクエストでは軽量な情報のみ返却
- ユーザー選択時に`codeAction/resolve`で詳細を取得

### 4. 実用的な大規模リファクタリング例

#### a) モジュール構造の再編成
```typescript
// LSPリクエスト例
{
  "method": "textDocument/codeAction",
  "params": {
    "textDocument": { "uri": "file:///src/index.ts" },
    "range": { /* 選択範囲 */ },
    "context": {
      "only": ["refactor.move"]
    }
  }
}
```

#### b) インターフェース抽出
```typescript
// 具体的なクラスから共通インターフェースを抽出
// LSPが自動的に：
// 1. インターフェースを生成
// 2. 実装クラスを更新
// 3. 参照箇所の型を変更
```

#### c) パラメータオブジェクト導入
```typescript
// 複数パラメータをオブジェクトに変換
// Before: function foo(a: string, b: number, c: boolean)
// After: function foo(params: { a: string, b: number, c: boolean })
// 全ての呼び出し箇所を自動更新
```

### 5. 制限事項と考慮点

1. **計算コスト**: 大規模プロジェクトでは編集計算に時間がかかる
2. **メモリ使用**: プロジェクト全体の解析にメモリを消費
3. **エディタ統合**: エディタによってサポートレベルが異なる

### 6. プログラマティックな使用

```typescript
// Node.jsからLSPを直接使用する例
import { LanguageClient } from 'vscode-languageclient/node';

// リファクタリング実行
const edits = await client.sendRequest('textDocument/codeAction', {
  textDocument: { uri: fileUri },
  range: selectionRange,
  context: { only: ['refactor'] }
});

// ワークスペース編集を適用
await client.sendRequest('workspace/applyEdit', {
  edit: edits[0].edit
});
```

## まとめ

TypeScript LSPは大規模リファクタリングに対応しており：
- プロジェクト全体のシンボル名変更
- モジュール構造の再編成
- 複数ファイルにまたがる一括変更
- プログラマティックなAPI経由での実行

これらはエディタのUIを介さず、LSPプロトコル経由で直接実行可能です。