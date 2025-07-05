# Conflict Resolution - 競合解決アルゴリズム

並行編集の競合を検出し、一貫性のある状態へ解決する戦略集。

## 責務

### 1. 基本戦略
```typescript
// Last Write Wins (LWW)
resolve([A@t1, B@t2]) → B

// Multi-Value Register (MVR)
resolve([A, B]) → {A, B} // 両方保持
```

### 2. 高度な解決
- **3-way merge**: 共通祖先からの差分マージ
- **Semantic merge**: ドメイン知識による解決
- **CRDT**: 競合フリーなデータ構造

### 3. 解決の記録
```typescript
// 競合履歴
{ 
  original: [A, B],
  resolved: C,
  strategy: "3way",
  timestamp: Date
}
```

## テスト対象

- 文字列の同時編集（OT/CRDT）
- カウンタの並行更新
- リスト操作の競合
- グラフ構造の変更
- カスタムルールの適用