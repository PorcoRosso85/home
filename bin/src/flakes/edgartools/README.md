# EdgarTools Nix Flake

SEC EDGAR データ分析ライブラリ [edgartools](https://github.com/dgunning/edgartools) のNix Flake実装。

## 特徴

- ✅ **Overlay対応**: 任意のPythonバージョンで利用可能
- ✅ **複数Python対応**: Python 3.9〜3.12をサポート
- ✅ **再現性**: Nixによる完全な依存関係管理
- ✅ **開発環境**: `nix develop`で即座に開発開始

## 使用方法

### 1. 他のFlakeから利用（Overlay使用）

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    edgartools.url = "github:yourusername/edgartools-flake";
  };

  outputs = { self, nixpkgs, edgartools }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        overlays = [ edgartools.overlays.${system}.default ];
      };
    in {
      # 任意のPythonバージョンで利用
      packages.${system}.myapp = pkgs.python312.withPackages (ps: [
        ps.edgartools  # overlayにより利用可能
        ps.pandas
        ps.jupyter
      ]);
    };
}
```

### 2. 直接実行

```bash
# 開発環境に入る
nix develop

# Python 3.11版を直接実行
nix run .#edgartools-py311 -- -c "from edgar import Company"

# Python 3.12版を直接実行  
nix run .#edgartools-py312 -- -c "from edgar import Company"
```

### 3. 開発環境

```bash
nix develop
python -c "from edgar import Company; print(Company('AAPL'))"
```

## Overlayテスト

呼び出し側が期待通りにoverlayできることを確認：

### 方法1: 組み込みチェック

```bash
# flake checkを実行（全Pythonバージョンでのimportテスト）
nix flake check

# 個別のチェック
nix build .#checks.x86_64-linux.overlay-py39
nix build .#checks.x86_64-linux.overlay-py312
```

### 方法2: テスト用Flake

```bash
cd test-overlay
nix run .#test-all
```

実行結果：
```
Testing edgartools overlay with multiple Python versions...

=== Python 3.9 ===
Python 3.9: ✓ edgar module imported

=== Python 3.10 ===
Python 3.10: ✓ edgar module imported

=== Python 3.11 ===
Python 3.11: ✓ edgar module imported

=== Python 3.12 ===
Python 3.12: ✓ edgar module imported

✅ All overlay tests passed!
```

### 方法3: 実際のプロジェクトでのテスト

別プロジェクトから以下のように利用してテスト：

```nix
# your-project/flake.nix
{
  inputs.edgartools.url = "path:/path/to/edgartools-flake";
  
  outputs = { self, nixpkgs, edgartools }:
    let
      pkgs = import nixpkgs {
        system = "x86_64-linux";
        overlays = [ edgartools.overlays.x86_64-linux.default ];
      };
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        packages = [
          (pkgs.python312.withPackages (ps: [ ps.edgartools ]))
        ];
      };
    };
}
```

## 実装のポイント

### Overlayの仕組み

```nix
overlays.default = final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (python-final: python-prev: {
      edgartools = buildEdgartools python-final;
    })
  ];
};
```

この実装により：
1. `pythonPackagesExtensions`を拡張
2. 任意のPythonバージョンの`ps.edgartools`が利用可能に
3. 利用側が自由にPythonバージョンを選択可能

## トラブルシューティング

### SHA256ハッシュの取得

初回ビルド時にエラーが出たら、正しいハッシュ値に置き換え：

```bash
nix build .#edgartools-py311
# エラーメッセージに正しいsha256が表示される
# flake.nixのsha256を更新
```

### Overlayが効かない場合

1. overlaysの適用順序を確認
2. systemアーキテクチャが一致しているか確認
3. `nix flake update`で入力を更新

## ライセンス

MIT License（edgartoolsのライセンスに準拠）