# KuzuDB TypeScript/Deno Packaging Solution

## 概要

このドキュメントは、`persistence/kuzu_ts`をnode_modules込みの完全なパッケージとして他プロジェクトから利用できるようにする解決策を説明します。

## 問題の背景

1. **Deno Worker制約**: npm:kuzuはWorker内で実行する必要があるが、Workerは呼び出し元プロジェクトのコンテキストで実行される
2. **ネイティブモジュール**: npm:kuzuはC++バインディングを含むため、ネットワークアクセスなしでのビルドが困難
3. **クロスプロジェクト利用**: sync/kuzu_tsから利用する際、node_modulesが必要

## 解決策: buildNpmPackage

NixのbuildNpmPackageを使用して、以下を実現:

### 1. 完全なパッケージング

```nix
packages.default = pkgs.buildNpmPackage rec {
  pname = "kuzu_ts";
  version = "0.1.0";
  
  src = ./.;
  
  # package-lock.jsonのハッシュ
  npmDepsHash = "sha256-eSa6agcAMBrN8aOEDsCMUNYfd73L4nYjseETXedz1AQ=";
  
  # Skip npm build since this is a Deno project
  dontNpmBuild = true;
  
  # ...
};
```

### 2. パッケージ構造

ビルド後のパッケージ構造:
```
/nix/store/xxxxx-kuzu_ts-0.1.0/
├── bin/
│   └── kuzu_ts           # ラッパースクリプト
└── lib/
    ├── kuzu_ts/          # Denoソースコード
    │   ├── core/
    │   ├── deps/
    │   ├── tests/
    │   ├── deno.json
    │   ├── mod.ts
    │   └── ...
    └── node_modules/     # npm依存関係
        └── kuzu_ts/
```

### 3. 利用方法

他プロジェクトから利用する場合:

```nix
{
  inputs = {
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
  };
  
  outputs = { self, kuzu-ts, ... }:
    let
      kuzuTsPackage = kuzu-ts.packages.${system}.default;
    in {
      # 直接インポート
      "${kuzuTsPackage}/lib/kuzu_ts/mod.ts"
    };
}
```

## 実装のポイント

### 1. npmDepsHashの取得

初回ビルド時に正しいハッシュ値を取得:
```bash
nix build
# エラーメッセージから正しいハッシュ値をコピー
# specified: sha256-XXXXX
# got:      sha256-eSa6agcAMBrN8aOEDsCMUNYfd73L4nYjseETXedz1AQ=
```

### 2. ネイティブモジュールのパッチ

C++ライブラリのパスを修正:
```nix
if [ -d "$out/lib/node_modules/kuzu" ]; then
  for lib in $out/lib/node_modules/kuzu/*.node; do
    if [ -f "$lib" ]; then
      ${pkgs.patchelf}/bin/patchelf \
        --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" \
        "$lib" || true
    fi
  done
fi
```

### 3. package.jsonの必須フィールド

buildNpmPackageにはnameとversionが必要:
```json
{
  "name": "kuzu_ts",
  "version": "0.1.0",
  "dependencies": {
    "kuzu": "^0.10.0"
  }
}
```

## 利点

1. **オフライン動作**: ビルド済みnode_modulesを含むため、ネットワーク不要
2. **再現性**: Nixの特性により、常に同じ結果を保証
3. **クロスプロジェクト対応**: 他プロジェクトから簡単に利用可能
4. **Git不要**: node_modulesをGitにコミットする必要なし

## テスト方法

```bash
# パッケージのビルド
nix build

# テスト実行
cd examples/test_package
nix run .#test
```

## 今後の改善案

1. **deno2nix**: より洗練されたDeno専用のパッケージング（現在は互換性に課題）
2. **FFI実装**: Worker不要な直接実装への移行
3. **WASM版**: ネイティブモジュール不要な実装への移行

## 参考資料

- [Nix buildNpmPackage documentation](https://nixos.org/manual/nixpkgs/stable/#javascript-buildNpmPackage)
- [Deno Worker API documentation](https://deno.land/api@v1.37.0?s=Worker)
- [KuzuDB npm package](https://www.npmjs.com/package/kuzu)