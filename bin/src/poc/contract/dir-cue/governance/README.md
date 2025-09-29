# Governance Flake System

## Overview

governance-flakeシステムは、Nixプロジェクトの構造とコントラクトを統一的に管理するためのスキーマ定義と検証システムです。

### 責務分離の原則

- **dir.cue**: プロジェクト方針の定義（技術語・依存関係の記述は禁止）
- **contracts/flake.cue**: 技術境界の強制（方針語の記述は禁止）

## Quick Start

### 1. governance-flakeの導入

```nix
# flake.nix
{
  inputs = {
    governance-flake.url = "path:../governance";
    # or git URL in production
  };

  outputs = { self, governance-flake, ... }: {
    # governance-flakeが提供するスキーマとチェックを利用
    checks = governance-flake.lib.validateProject ./.;
  };
}
```

### 2. プロジェクト構造の定義

#### dir.cue (プロジェクト方針)
```cue
// 技術語・依存関係の記述は禁止
// 方針のみを記述
project: {
    name: "my-project"
    purpose: "ユーザー管理システム"
    target_audience: "エンドユーザー"
}

structure: close({
    apps?: [...string]
    libs?: [...string]
    services?: [...string]
})
```

#### contracts/flake.cue (技術境界)
```cue
// 方針語の記述は禁止
// 技術的制約のみを記述
import "github.com/my-org/governance-flake/schema"

flake: schema.#FlakeContract & {
    inputs: close({
        nixpkgs: _
        flake-utils: _
    })

    outputs: close({
        packages: _
        apps?: _
        devShells?: _
    })
}
```

## 運用ルール

### Definition of Done (DoD)

プロジェクトが以下すべてを満たす場合のみ、governance準拠とみなします：

1. **スキーマ準拠**: すべてのclose構造で追加フィールド禁止が実装済み
2. **責務分離**: dir.cueに技術語・依存混入なし、contracts/flake.cueに方針語混入なし
3. **純粋評価**: チェックは作業ツリーに生成物を書かない
4. **整合性**: exports重複検知とdependsOn参照検証が機能
5. **統合検証**: `nix flake check -L`が成功
6. **互換性**: 既存プロジェクトはアダプタ経由で段階的移行可能

### レビュー観点チェックリスト

#### dir.cue レビューポイント
- [ ] 技術実装詳細（言語、フレームワーク、ライブラリ）が記述されていない
- [ ] 具体的な依存関係が記述されていない
- [ ] ビジネス方針・目的・対象者のみが記述されている
- [ ] close構造により追加フィールドが禁止されている

#### contracts/flake.cue レビューポイント
- [ ] ビジネス方針・目的が記述されていない
- [ ] 技術的制約・境界のみが記述されている
- [ ] inputs/outputsがclose構造で制限されている
- [ ] スキーマインポートが正しく行われている

#### システム全体
- [ ] `nix flake check -L`が成功する
- [ ] exports一意性検証が動作する
- [ ] dependsOn参照検証が動作する
- [ ] 互換性アダプタが既存契約をサポートする

## トラブルシューティング

### よくあるエラーと対処法

#### 1. "field not allowed" エラー
```
error: field "unexpected_field" not allowed
```

**原因**: close構造で定義されていないフィールドを追加

**対処法**:
- dir.cueまたはcontracts/flake.cueで該当フィールドが許可されているか確認
- 不要なフィールドであれば削除
- 必要なフィールドであればスキーマを更新

#### 2. 責務分離違反エラー
```
error: technical terms found in dir.cue
```

**原因**: dir.cueに技術実装詳細を記述

**対処法**:
- 技術的内容をcontracts/flake.cueに移動
- dir.cueはビジネス方針のみに限定

#### 3. exports重複エラー
```
error: duplicate export name "my-app" found
```

**原因**: 複数のプロジェクトで同一のexport名を使用

**対処法**:
- export名を一意にリネーム
- プロジェクト固有のプレフィックスを追加

### デバッグ手順

1. **基本チェック**
   ```bash
   nix flake check -L
   ```

2. **CUE評価の詳細確認**
   ```bash
   cd governance
   cue eval ./...
   ```

3. **アダプタ動作確認**
   ```bash
   cue eval -e adapter adapter/compat.cue test_migration_scenario.cue
   ```

## Migration Guide

### 既存プロジェクトの段階的移行

#### Phase 1: アダプタ導入
```bash
# 1. governance-flakeを inputs に追加
# 2. 互換性アダプタを有効化
# 3. 段階的にスキーマ準拠に移行
```

#### Phase 2: スキーマ移行
```bash
# 1. 既存の設定をdir.cueとcontracts/flake.cueに分離
# 2. 責務分離の確認
# 3. close構造の適用
```

#### Phase 3: 完全移行
```bash
# 1. アダプタの無効化
# 2. 新スキーマでの完全動作確認
# 3. DoD達成の確認
```

## 継続的メンテナンス

### 定期チェック項目

1. **月次**: 全プロジェクトでのgovernance準拠状況確認
2. **リリース前**: DoD完全達成の確認
3. **年次**: スキーマバージョンアップデートの検討

### バージョン管理

- **MAJOR**: 破壊的変更（既存契約に非互換性）
- **MINOR**: 後方互換性のある新機能追加
- **PATCH**: バグ修正・改善

## Risk Management

### 主要リスク

1. **既存契約不整合**: アダプタ+allowlistで対応
2. **スキーマ変更影響**: SemVerベースの段階的移行
3. **責務分離違反**: 自動チェックと継続的レビューで防止

### 対策

- 互換性アダプタによる段階的移行サポート
- 自動検証による早期エラー検知
- 明確なDoD基準による品質保証

## Examples

### 完全なプロジェクト例

サンプル実装は `/apps/sample-app/` を参照してください。

- dir.cue: ビジネス方針の定義例
- contracts/flake.cue: 技術境界の定義例
- flake.nix: governance-flake統合例

## Support

### 問い合わせ先

- スキーマ関連: governance/schema/types.cue 参照
- アダプタ関連: governance/adapter/ 参照
- 実装例: apps/sample-app/ 参照