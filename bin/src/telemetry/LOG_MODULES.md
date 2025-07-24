# Log Modules - Flake-based Telemetry Logging

言語別に独立したFlakeとして提供されるログモジュール群。

## 概要

各言語のログモジュールは独立したNix Flakeとして提供され、他のプロジェクトからflake inputとして利用できます。

## ディレクトリ構造

```
telemetry/
├── log_py/        # Python実装
│   ├── flake.nix
│   ├── log_py/
│   │   ├── __init__.py
│   │   ├── domain.py
│   │   ├── application.py
│   │   ├── infrastructure.py
│   │   └── variables.py
│   └── tests/
├── log_ts/        # TypeScript実装
│   ├── flake.nix
│   ├── mod.ts
│   ├── domain.ts
│   ├── application.ts
│   ├── infrastructure.ts
│   └── variables.ts
└── example-app/   # 使用例
```

## 使用方法

### 1. Flake Inputとして追加

```nix
# あなたのプロジェクトのflake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    
    # ログモジュールを追加
    log-ts.url = "path:/home/nixos/bin/src/telemetry/log_ts";
    log-py.url = "path:/home/nixos/bin/src/telemetry/log_py";
  };

  outputs = { self, nixpkgs, log-ts, log-py, ... }:
    # ...
}
```

### 2. TypeScriptでの使用

```typescript
// Flakeが提供するパスを使用
import { log } from "${log-ts.lib.importPath}/mod.ts";

// ログ出力
log("INFO", { 
  uri: "/api/users", 
  message: "User created", 
  userId: "123" 
});
// 出力: {"level":"INFO","uri":"/api/users","message":"User created","userId":"123"}
```

### 3. Pythonでの使用

```python
from log_py import log

# ログ出力
log("ERROR", {
    "uri": "/api/auth",
    "message": "Authentication failed",
    "error_code": "AUTH_001"
})
# 出力: {"level":"ERROR","uri":"/api/auth","message":"Authentication failed","error_code":"AUTH_001"}
```

## API仕様

### 共通インターフェース

```
log(level: string, data: LogData)
```

- **level**: ログレベル（任意の文字列: "INFO", "ERROR", "DEBUG", "METRIC" など）
- **data**: ログデータオブジェクト
  - **uri** (必須): 発生場所を示すURI
  - **message** (必須): ログメッセージ
  - **その他**: 任意のフィールドを追加可能

### 出力形式

- **形式**: JSONL（1行1JSON）
- **出力先**: 標準出力（stdout）
- **エンコーディング**: UTF-8

## 実装の特徴

### DDD構造

両言語とも同じDDD層構造で実装：

- **domain**: ビジネスロジック（LogData型、to_jsonl関数）
- **application**: APIの実装（log関数）
- **infrastructure**: 外部依存（stdout出力）
- **variables**: 環境変数管理（将来の拡張用）

### 設計原則

1. **最小限のAPI**: `log(level, data)` のみ
2. **型安全**: 各言語の型システムを活用
3. **拡張可能**: dataフィールドは自由に追加可能
4. **非侵襲的**: アプリケーションに制約を課さない
5. **テスト容易**: 外部プロセスとして振る舞いテスト可能

## 開発

### テスト実行

```bash
# TypeScriptモジュール
cd telemetry/log_ts
nix run .#test

# Pythonモジュール（ビルド問題解決後）
cd telemetry/log_py
nix run .#test
```

### 開発環境

```bash
# 開発シェルに入る
nix develop

# REPLでテスト
nix run .#repl
```

## 動作状況

- **TypeScript版**: ✅ 完全動作
- **Python版**: ✅ ビルド成功（テストはパス問題で失敗）

### Pythonモジュールの注意点

ビルドは成功しますが、外部プロセスとして実行する振る舞いテストは、インポートパスの問題で失敗します。通常の使用（flake inputとして利用）では問題ありません。

## 今後の拡張

- Go実装の追加（`log_go/`）
- Rust実装の追加（`log_rs/`）
- 共通テストスイートの整備
- パフォーマンスベンチマーク