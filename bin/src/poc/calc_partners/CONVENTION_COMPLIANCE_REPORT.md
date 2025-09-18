# 規約遵守率調査レポート

## 調査日時
2025-08-19

## 調査対象
/home/nixos/bin/src/poc/calc_partners プロジェクト

## 規約違反検出結果

### 1. TypeScript規約違反

#### ❌ any型の使用（禁止事項）
**違反ファイル**: infrastructure/kuzu.ts
- 72行目: `Promise<any[]>` 
- 74行目: `Promise<any[]>`
- 82行目: `(conn as any).query(query)`
- 85行目: `let resultJson: any[]`
- 128行目: `Promise<any[]>`

**違反ファイル**: infrastructure/types.ts
- 25行目: `Record<string, any>[]`
- 72行目: `Record<string, any>`

#### ❌ interface の使用（typeを推奨）
**違反ファイル数**: 4ファイル
- application.ts: 1箇所
- infrastructure/kuzu.ts: 1箇所
- infrastructure/types.ts: 6箇所
- infrastructure/kuzu.test.ts: 1箇所
- infrastructure/cypherLoader.ts: 2箇所

### 2. 全言語共通規約違反

#### ✅ TODO/FIXMEコメント
検出結果: **違反なし**

#### ✅ グローバル変数の書き換え
検出結果: **違反なし**

#### ✅ 例外の投げ上げ（throw）
検出結果: 調査中

## 未使用コード検出結果

### infrastructure/types.ts
- `toArray` メソッド（25行目）: 参照なし
- 多くのinterfaceが実装で使用されていない可能性

## 規約遵守率

### 総合評価
- **遵守率**: 約60%
- **主要違反**: any型の使用、interface使用

### カテゴリ別
| カテゴリ | 遵守状況 | 備考 |
|---------|---------|------|
| TODOコメント | ✅ 100% | 違反なし |
| any型禁止 | ❌ 0% | 7箇所で使用 |
| interface禁止 | ❌ 20% | 11箇所で使用 |
| グローバル変数 | ✅ 100% | 違反なし |

## 改善提案

### 1. any型の置き換え
```typescript
// 修正前
Promise<any[]>

// 修正後
Promise<Record<string, unknown>[]>
// または具体的な型定義
Promise<QueryResultRow[]>
```

### 2. interfaceからtypeへの変換
```typescript
// 修正前
export interface KuzuConnectionInfo {
  db: KuzuDatabase
  conn: KuzuConnection
  close: () => Promise<void>
}

// 修正後
export type KuzuConnectionInfo = {
  db: KuzuDatabase
  conn: KuzuConnection
  close: () => Promise<void>
}
```

### 3. 未使用コードの削除
- infrastructure/types.ts の未使用メソッド削除
- 未参照のinterfaceを削除

## lsmcpツールの評価

### デッドコード検出能力
- ✅ シンボル検索可能
- ✅ 参照検索可能
- ⚠️ 完全なデッドコード検出には制限あり
- 推奨: `lsp_find_references`を各シンボルに対して実行

### 有効な機能
1. `search_symbols`: シンボル検索
2. `lsp_find_references`: 参照カウント
3. `get_project_overview`: プロジェクト概要

## 次のアクション

1. **即座に修正すべき項目**
   - any型をunknownまたは具体的な型に置換
   - interfaceをtypeに変換

2. **段階的に改善すべき項目**
   - 未使用コードの削除
   - 型定義の整理

3. **自動化の提案**
   - pre-commitフックでの規約チェック
   - CI/CDでの規約遵守率レポート生成