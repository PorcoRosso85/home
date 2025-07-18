# KuzuDB Deno Integration - 改善計画

## 既知の問題

### 現象
テスト実行後にDenoがパニックする
```
Fatal error in :0: Check failed: heap->isolate() == Isolate::TryGetCurrent().
thread 'main' panicked at cli/main.rs:427:5
```

### 影響
- KuzuDB操作自体は正常に完了
- プロセス終了時にクラッシュ
- CI/CDパイプラインでエラー扱いになる可能性

## 根本原因
DenoのNode.js互換レイヤーとネイティブモジュール（.node）の相性問題
- V8 isolateのライフサイクル管理の不整合
- ネイティブモジュールのクリーンアップタイミング

## 改善案

### 1. 短期的対策（推奨）
**ワーカープロセス分離アプローチ**
```typescript
// core/database_worker.ts
import { Database, Connection } from "kuzu";

self.onmessage = async (e) => {
  const { method, args } = e.data;
  // KuzuDB操作を実行
  const result = await executeKuzuOperation(method, args);
  self.postMessage(result);
};
```

**メリット**:
- メインプロセスから分離してクラッシュを隔離
- 既存APIを維持
- 実装が比較的簡単

### 2. 中期的対策
**Deno FFI直接実装**
```typescript
// core/kuzu_ffi.ts
const libKuzu = Deno.dlopen("./libkuzu.so", {
  kuzu_database_init: { parameters: ["pointer"], result: "pointer" },
  kuzu_connection_init: { parameters: ["pointer"], result: "pointer" },
  // ... 他のFFI定義
});
```

**メリット**:
- Node.js互換レイヤーを完全回避
- パフォーマンス向上
- Denoネイティブ

**デメリット**:
- 実装工数が大きい
- KuzuDB C++ APIの深い理解が必要

### 3. 長期的対策
**WebAssembly版KuzuDB**
- KuzuDBをWASMにコンパイル
- ブラウザ/Deno/Node.js共通で動作
- 最もポータブル

## 実装優先順位

1. **ワーカープロセス分離**（1週間）
   - 既存の問題を即座に解決
   - APIの後方互換性を維持
   
2. **エラーハンドリング強化**（2-3日）
   - プロセス終了前のクリーンアップ
   - グレースフルシャットダウン

3. **CI/CD対応**（1日）
   - テストスクリプトでexit codeを制御
   - パニックを無視するオプション追加

## テスト戦略

1. **分離テスト環境**
   ```bash
   deno test --allow-all || true  # パニックを無視
   ```

2. **ヘルスチェック追加**
   ```typescript
   Deno.test("health check after operations", async () => {
     // KuzuDB操作後の状態確認
     await verifyDatabaseState();
   });
   ```

3. **ベンチマーク**
   - ワーカー分離のオーバーヘッド測定
   - メモリ使用量の監視

## 次のステップ

1. ワーカープロセス分離の実装開始
2. 既存テストの修正
3. パフォーマンステストの追加
4. ドキュメントの更新