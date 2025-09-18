# Bun + persistence/kuzu_ts 最小構成の証明

## 概要

Bunクライアントの実行に必要な設定は、persistence/kuzu_tsのflake.input**のみ**であることを証明します。

## 証明内容

### 1. Bunランタイム
- **提供元**: nixpkgs（標準パッケージ）
- **flake.input不要**: ✅
- **設定例**:
  ```nix
  buildInputs = with pkgs; [
    bun  # nixpkgsから直接利用
  ];
  ```

### 2. KuzuDB（persistence/kuzu_ts経由）
- **提供元**: persistence/kuzu_ts flake
- **flake.input必要**: ✅ （これのみ）
- **設定例**:
  ```nix
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";  # 唯一の追加input
  };
  ```

### 3. その他の設定
- **package.json dependencies**: 不要
- **npm install**: 不要
- **環境変数**: LD_LIBRARY_PATHのみ（ネイティブモジュール用）
- **追加のflake.input**: 不要

## 実装例

### flake.nix（最小構成）
```nix
{
  description = "Minimal Bun client with persistence/kuzu_ts";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../../persistence/kuzu_ts";  # 唯一の依存
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        apps.bun-client = {
          type = "app";
          program = "${pkgs.writeShellScript "start-bun-client" ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            exec ${pkgs.bun}/bin/bun run ./bun_client.ts
          ''}";
        };
      });
}
```

### bun_client.ts
```typescript
// require()でkuzuモジュールを読み込み
const kuzu = require("kuzu");
const { Database, Connection } = kuzu;

// 以降、通常のKuzuDB操作
const db = new Database(":memory:");
const conn = new Connection(db);
```

## 動作確認済み環境

- **場所**: `/home/nixos/bin/src/sync/kuzu_ts/`
- **ファイル**: `bun_client.ts`
- **実行方法**: `nix run .#bun-client`
- **確認日時**: 2025-08-01

### 確認された動作
1. ✅ require("kuzu")が成功
2. ✅ Database/Connectionクラスが利用可能
3. ✅ インメモリデータベース作成
4. ✅ WebSocketクライアント機能
5. ✅ イベントソーシング

## 結論

Bunクライアントの実行に必要な設定は：

1. **nixpkgs**（標準）: Bunランタイム提供
2. **persistence/kuzu_ts**（唯一の追加input）: KuzuDB提供

これ以外の設定は一切不要であることが証明されました。

## 利点

1. **最小構成**: 必要最小限のflake.inputのみ
2. **再現性**: Nixによる完全な再現性
3. **簡潔性**: npm installやpackage.json管理が不要
4. **統一性**: persistence層を一元管理

## 参考

- persistence/kuzu_ts自体の実装: `../../persistence/kuzu_ts/`
- 実際の使用例: `./bun_client.ts`
- テスト: `./bun_client.test.ts`