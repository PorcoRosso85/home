# Embed POC - 引き継ぎドキュメント

## 現状と課題

### 1. 現在の問題点

#### 依存関係の問題
- asvs_referenceパッケージへの依存が相対パスで解決されている
- PYTHONPATHに依存した構造
- PyTorchなどの重い依存関係によりビルドがタイムアウト

#### パッケージ構造の問題
現在のインポート：
```python
from asvs_reference.reference_repository import create_reference_repository
```
これはasvs_referenceがパッケージ化されていないため動作しません。

### 2. 修正手順

#### Step 1: パッケージ構造の整備
```bash
# 1. パッケージディレクトリの作成
mkdir -p embed_pkg
mv embedding_repository.py embed_pkg/
mv demo_embedding_similarity.py embed_pkg/
mv embeddings embed_pkg/
touch embed_pkg/__init__.py

# 2. pyproject.tomlの更新
[tool.setuptools.packages.find]
where = ["."]
include = ["embed_pkg*"]

# 3. インポートの修正
# embed_pkg/embedding_repository.py:
from asvs_reference_pkg.reference_repository import create_reference_repository, DatabaseError, ValidationError
```

#### Step 2: flake.nixの完全な書き換え
```nix
{
  description = "Embedding and Similarity Search POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python311;
        
        # asvs_referenceパッケージ
        asvs_reference = python.pkgs.buildPythonPackage {
          pname = "asvs-reference";
          version = "0.1.0";
          src = ../asvs_reference;
          propagatedBuildInputs = with python.pkgs; [
            pyyaml
            jinja2
          ];
        };
        
        # embedパッケージ
        embedPkg = python.pkgs.buildPythonPackage {
          pname = "embed-pkg";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with python.pkgs; [
            asvs_reference
            sentence-transformers
            torch
            transformers
            numpy
          ];
          
          format = "pyproject";
          
          nativeBuildInputs = with python.pkgs; [
            setuptools
            wheel
          ];
        };
        
      in
      {
        packages.default = embedPkg;
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${self}
              exec ${python.withPackages (ps: [embedPkg pytest])}/bin/pytest test_embedding_repository.py -v
            ''}";
          };
          
          test-external = {
            type = "app";
            program = "${pkgs.writeShellScript "test-external" ''
              cd ${self}/e2e/external
              exec ${python.withPackages (ps: [embedPkg pytest])}/bin/pytest test_package.py -v
            ''}";
          };
        };
      }
    );
}
```

#### Step 3: 依存関係の最適化
```toml
# pyproject.tomlで最小限の依存を指定
[project]
dependencies = [
    "asvs-reference",  # 隣のPOCに依存
    "sentence-transformers>=2.2.0",
    "torch>=2.0.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

#### Step 4: E2Eテストの作成
```python
# e2e/external/test_package.py
"""
External package test following nix_flake conventions
"""
def test_embed_package_importable():
    """Test that the package can be imported"""
    import embed_pkg
    assert embed_pkg is not None

def test_embedding_repository_available():
    """Test that embedding repository can be created"""
    from embed_pkg.embedding_repository import create_embedding_repository
    # メモリDBでテスト
    repo = create_embedding_repository(":memory:")
    assert "save_with_embedding" in repo

def test_embedder_types_available():
    """Test that embedder types are available"""
    from embed_pkg.embeddings.base import create_embedder
    # エラーハンドリングのテスト
    result = create_embedder("invalid-model", "invalid-type")
    assert result.get("ok") is False
```

### 3. ビルド時間の改善

#### キャッシュの活用
```bash
# 事前にダウンロード
nix build .#embedPkg.propagatedBuildInputs --no-link

# または軽量モデルの使用
model_name = "all-MiniLM-L6-v2"  # より小さいモデル
```

#### オプション: CPUのみのPyTorch
```nix
# flake.nixで
torch-cpu = python.pkgs.torch.override { cudaSupport = false; };
```

### 4. 期待される最終状態

1. **独立したパッケージ**: 他のPOCからインポート可能
2. **ビルド時間の改善**: 5分以内でビルド完了
3. **すべてのテストがパス**: 9個のテスト + E2Eテスト

### 5. 完了基準

- [ ] embed_pkgディレクトリにすべてのPythonファイルが移動
- [ ] pyproject.tomlが正しく設定されている
- [ ] flake.nixからPYTHONPATH設定が削除されている
- [ ] asvs_referenceへの依存が正しく解決される
- [ ] `nix run .#test`で全テストがパス
- [ ] `nix run .#test-external`でE2Eテストがパス
- [ ] ビルド時間が5分以内

## トラブルシューティング

### Q: ビルドがまだタイムアウトする
A: 以下を試す：
1. `nix.conf`に`substituters = https://cache.nixos.org`を追加
2. より小さいモデル（distilbert-base-uncased）を使用
3. CPUのみのPyTorchを使用

### Q: asvs_referenceが見つからない
A: asvs_referenceも先にパッケージ化が完了している必要があります

### Q: テストで"KeyError: 'save_with_embedding'"
A: create_reference_repositoryが正しく動作していない可能性。asvs_referenceのテストを先に確認

### Q: メモリ不足エラー
A: テスト時により小さいバッチサイズを使用：
```python
embedder = create_embedder(model_name, batch_size=8)  # デフォルトは32
```

## 追加の推奨事項

1. **CI/CD統合**: GitHub ActionsでNixビルドをキャッシュ
2. **ドキュメント**: 各関数のdocstringを充実させる
3. **パフォーマンステスト**: 大量データでの動作確認
4. **エラーハンドリング**: より詳細なエラーメッセージ