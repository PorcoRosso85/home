# KuzuDB クエリシステム汎用化リファクタリング作業手順書

## 作業概要
- **目標**: 個別ラッパー関数を完全削除し、完全自動化された汎用クエリシステムを構築
- **期待効果**: 696行 → 300-400行 (50-60%削減)、手動レジストリ不要、完全自動テンプレート検出

## 現在の問題
- 旧システムとの共存により複雑化（コード量4%増）
- 個別ラッパー関数が大量残存（1,300+行）
- 手動レジストリが必要
- 完全自動化が未完成

---

## Phase 1: 汎用システム完成 (1-2時間) 【最優先】

### 1.1 queryService.ts の完全自動検出機能追加

**ファイル**: `query/application/services/queryService.ts`

**現在の問題**: テンプレート存在チェックが手動
**作業内容**: 
```typescript
// 追加すべき機能
export async function executeAnyTemplate(
  connection: any,
  templateName: string, 
  params: Record<string, any> = {}
): Promise<QueryResult> {
  // 1. DMLディレクトリで検索
  // 2. DQLディレクトリで検索  
  // 3. 自動的にパラメータ検証
  // 4. 適切なリポジトリ関数呼び出し
}
```

### 1.2 templateScanner.ts の完全自動化機能追加

**ファイル**: `query/application/services/templateScanner.ts`

**現在の問題**: 手動でディレクトリ指定が必要
**作業内容**:
```typescript
// 追加すべき機能
export function createAutoTemplateScanner() {
  return {
    // DML/DQL両方を自動スキャン
    scanAllTemplates: () => Promise<TemplateRegistry>,
    // テンプレート名から自動的にタイプ判定
    detectTemplateType: (name: string) => 'dml' | 'dql',
    // パラメータ自動抽出
    extractParams: (templateContent: string) => string[]
  };
}
```

### 1.3 統一APIエントリーポイント作成

**新規ファイル**: `query/application/services/unifiedQueryService.ts`

**作業内容**: 
```typescript
/**
 * 統一クエリAPI - 最終的にこの2つだけがexportされる
 */

// DMLクエリ実行（作成・更新・削除）
export async function executeDml(
  connection: any,
  templateName: string, 
  params: Record<string, any>
): Promise<QueryResult>

// DQLクエリ実行（検索・取得）  
export async function executeDql(
  connection: any,
  templateName: string,
  params: Record<string, any>
): Promise<QueryResult>

// 自動判定版（推奨）
export async function executeTemplate(
  connection: any,
  templateName: string,
  params: Record<string, any>
): Promise<QueryResult>
```

### 1.4 Phase 1 完了確認

**テストコマンド**:
```bash
cd /home/nixos/bin/src/kuzu

# 新しい汎用APIが動作することを確認
npm test -- --grep "unified"

# ビルドエラーがないことを確認  
npm run build
```

**成功基準**: 
- [ ] 新しい汎用API 3つが正常動作
- [ ] 任意のテンプレート名で自動実行可能
- [ ] パラメータ自動検証が動作
- [ ] ビルドエラーなし

---

## Phase 2: 依存関係調査・修正 (1時間)

### 2.1 削除対象への依存関係調査

**調査コマンド**:
```bash
cd /home/nixos/bin/src/kuzu

# integratedDmlService への依存を調査
grep -r "from.*integratedDmlService\|import.*integratedDmlService" . --include="*.ts"

# dmlOperations への依存を調査  
grep -r "from.*dmlOperations\|import.*dmlOperations" . --include="*.ts"

# versionProgressOperations への依存を調査
grep -r "from.*versionProgressOperations\|import.*versionProgressOperations" . --include="*.ts"

# 個別関数の使用箇所を調査
grep -r "createLocationURI\|createCodeEntity\|createRequirement" . --include="*.ts"
```

### 2.2 修正対象ファイルリスト作成

**調査結果記録**:
```
修正が必要なファイル:
- query/index.ts (export文修正)
- query/interface/versionProgressOperations.ts (import修正)  
- その他の使用箇所... (上記コマンドで特定)
```

### 2.3 呼び出し元を汎用APIに変更

**修正パターン**:
```typescript
// 変更前
import { createLocationURI } from './services/integratedDmlService';
await createLocationURI(conn, 'id', 'file', '/path');

// 変更後  
import { executeDml } from './services/unifiedQueryService';
await executeDml(conn, 'create_locationuri', {
  uri_id: 'id', scheme: 'file', path: '/path'
});
```

### 2.4 Phase 2 完了確認

**確認事項**:
- [ ] 全ての依存関係を特定完了
- [ ] 修正対象ファイルリスト作成完了
- [ ] 修正パターンを決定完了
- [ ] ビルドエラーなし

---

## Phase 3: 段階的削除 (2-3時間)

### 3.1 integratedDmlService.ts 削除

**削除対象**: `query/application/services/integratedDmlService.ts` (230行)

**作業手順**:
1. ファイル削除
2. import修正（Phase 2で特定した箇所）
3. ビルドテスト
4. 動作テスト

**削除後テスト**:
```bash
# ビルド確認
npm run build

# 汎用API動作確認
npm test -- --grep "template"
```

### 3.2 interface層の大量削除

**削除対象**:
- `query/interface/dmlOperations.ts` (611行)
- `query/interface/versionProgressOperations.ts` (459行)  
- `query/interface/queryClient.ts` (調査後)
- `query/interface/queryExecutor.ts` (調査後)

**作業手順** (1ファイルずつ):
1. ファイル削除
2. import修正
3. ビルドテスト  
4. 次のファイルへ

**重要**: 必ず1ファイルずつ削除してテストを実行

### 3.3 Phase 3 完了確認

**成功基準**:
- [ ] interface層から1,000+行削除完了
- [ ] 個別ラッパー関数が完全削除
- [ ] ビルドエラーなし
- [ ] 基本動作テスト成功

---

## Phase 4: エクスポート整理・最終確認 (30分)

### 4.1 index.ts の大幅削除

**ファイル**: `query/index.ts`

**変更内容**:
```typescript
// 変更前: 50+ の個別関数をexport
export * from './interface/dmlOperations';
export * from './interface/versionProgressOperations';
// ... 大量のexport

// 変更後: 汎用API 2-3個のみ
export { executeDml, executeDql, executeTemplate } from './application/services/unifiedQueryService';
export * from './domain/types/queryTypes';  // 型定義は維持
export * from './application/validation/templateValidator';  // バリデーションは維持
```

### 4.2 物理削除

**削除対象**:
```bash
rm query/application/services/dmlService.ts.deleted
rm query/application/services/versionProgressService.ts.deleted
```

### 4.3 最終動作テスト

**テストシナリオ**:
```typescript
// テストケース1: DML実行
await executeDml(connection, 'create_locationuri', {
  uri_id: 'test', scheme: 'file', path: '/test'
});

// テストケース2: DQL実行  
await executeDql(connection, 'get_version_statistics_details', {
  version_id: 'v1.0.0'
});

// テストケース3: 自動判定
await executeTemplate(connection, 'create_codeentity', {
  persistent_id: 'test', name: 'Test'
});
```

### 4.4 Phase 4 完了確認

**最終成功基準**:
- [ ] export関数が汎用API 2-3個のみ
- [ ] 全ての削除ファイルが物理削除完了
- [ ] 全機能が汎用APIで動作確認
- [ ] コード量50-60%削減達成
- [ ] 新しいテンプレート追加時の手動作業0

---

## 最終的な構成

### 残存ファイル (約300-400行)
- `unifiedQueryService.ts` (~80行) - 汎用API
- `queryService.ts` (~60行) - 自動検出機能  
- `templateScanner.ts` (~70行) - 完全自動化
- バリデーション層 (170行) - 必要機能
- 型定義 (125行) - 必要機能

### 削除されるファイル (1,300+行)
- `integratedDmlService.ts` (230行)
- `dmlOperations.ts` (611行)
- `versionProgressOperations.ts` (459行)
- その他 interface層

### 新しい使用方法
```typescript
// たった1行でどんなクエリでも実行可能
await executeTemplate(connection, 'any_template_name', params);
```

---

## 作業再開時のチェックリスト

**現在の状況確認**:
- [ ] Phase 1完了状況を確認
- [ ] Phase 2の依存関係調査状況を確認  
- [ ] Phase 3の削除進捗を確認
- [ ] ビルドエラーの有無を確認

**作業再開手順**:
1. 現在のPhaseを特定
2. 該当Phaseの完了確認を実行
3. 次のPhaseに進む
4. 問題発生時は前のPhaseに戻って確認

**緊急時の復旧**:
```bash
# 作業前の状態に戻す
git reset --hard HEAD~1

# 特定ファイルのみ復旧
git checkout HEAD~1 -- path/to/file
```
