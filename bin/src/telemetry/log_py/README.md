# log_py - Python Universal Log API

統一的なログAPI仕様のPython実装。`log = stdout` の原則に基づく。

## インストール

### Flake Inputとして

```nix
{
  inputs.log-py.url = "path:../telemetry/log_py";
  
  outputs = { self, nixpkgs, log-py, ... }:
    let
      pkgs = import nixpkgs {
        overlays = [ log-py.overlays.default ];
      };
    in {
      # Python環境で使用
      devShells.default = pkgs.mkShell {
        buildInputs = [
          (pkgs.python3.withPackages (ps: [ ps.log_py ]))
        ];
      };
    };
}
```

## 使用方法

```python
from log_py import log

# 基本的な使用
log("INFO", {"uri": "/api/users", "message": "User created", "userId": "123"})

# エラーログ
log("ERROR", {
    "uri": "/api/auth",
    "message": "Authentication failed",
    "error_code": "AUTH_001"
})

# メトリクス
log("METRIC", {
    "uri": "/metrics",
    "message": "Performance data",
    "latency": 42.5,
    "request_count": 100
})
```

## API

### log(level: str, data: dict) → None

- **level**: ログレベル（任意の文字列）
- **data**: ログデータ（必須: uri, message）
  - **uri**: 発生場所のURI
  - **message**: ログメッセージ
  - その他の任意フィールド

出力: stdout へのJSONL形式

### to_jsonl(data: dict) → str

辞書をJSONL形式の文字列に変換

## 開発

```bash
# 開発環境
nix develop

# テスト実行
nix run .#test

# REPL
nix run .#repl
```

## アーキテクチャ

DDD（ドメイン駆動設計）構造：
- `domain.py`: ビジネスロジック（LogData型、to_jsonl関数）
- `application.py`: ユースケース（log関数）
- `infrastructure.py`: 技術詳細（stdout出力）
- `variables.py`: 環境変数管理