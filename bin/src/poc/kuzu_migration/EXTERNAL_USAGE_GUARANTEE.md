# architecture/ddlチームへ：外部使用の担保方法

## 概要
POCで実証済みの「外部から安全に使用できることを担保する方法」をお伝えします。

## 1. Nix Flakeによる完全な依存関係管理

### flake.nixでの公開方法
```nix
# kuzu_migration/flake.nix
{
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        kuzu-migrate = pkgs.writeShellApplication {
          name = "kuzu-migrate";
          runtimeInputs = with pkgs; [ kuzu coreutils ];
          text = builtins.readFile ./src/kuzu-migrate.sh;
        };
      in
      {
        # パッケージとして公開
        packages.default = kuzu-migrate;
        
        # ライブラリ関数として公開
        lib.mkKuzuMigration = { pkgs, ddlPath ? "./ddl" }: {
          init = {
            type = "app";
            program = "${self.packages.${pkgs.system}.default}/bin/kuzu-migrate --ddl ${ddlPath} init";
          };
          migrate = {
            type = "app";
            program = "${self.packages.${pkgs.system}.default}/bin/kuzu-migrate --ddl ${ddlPath} apply";
          };
          # ... 他のコマンド
        };
      });
}
```

### 外部プロジェクトでの使用方法
```nix
# 外部プロジェクトのflake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    kuzu-migration.url = "github:yourorg/kuzu-migration";
  };

  outputs = { self, nixpkgs, kuzu-migration }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      # 方法1: 直接パッケージを使用
      apps.migrate = {
        type = "app";
        program = "${kuzu-migration.packages.${system}.default}/bin/kuzu-migrate";
      };
      
      # 方法2: lib関数を使用
      apps = kuzu-migration.lib.mkKuzuMigration {
        inherit pkgs;
        ddlPath = "./my-ddl";
      };
    };
}
```

## 2. テストによる担保

### 2.1 External E2Eテスト構造
```
tests/e2e/
├── internal/      # 内部動作テスト
└── external/      # 外部使用テスト ← これが担保
    ├── flake.nix  # 独立したflakeとして動作確認
    ├── test_e2e_flake_integration.py
    └── test_e2e_cli_import.py
```

### 2.2 外部テストの実装例
```python
# tests/e2e/external/test_e2e_flake_integration.py
class TestMkKuzuMigrationFunction:
    def test_external_flake_can_use_mkKuzuMigration(self):
        """外部flakeがlib.mkKuzuMigrationを使用できることを確認"""
        # 1. 外部プロジェクトのflake.nixを作成
        # 2. nix flake showで確認
        # 3. 各コマンドが実行可能か検証
```

### 2.3 CIでの自動検証
```yaml
# .github/workflows/test.yml
- name: Test External Usage
  run: |
    cd tests/e2e/external
    nix flake check
    nix run .#test
```

## 3. 依存関係の完全性

### writeShellApplicationの利点
```nix
kuzu-migrate = pkgs.writeShellApplication {
  name = "kuzu-migrate";
  runtimeInputs = with pkgs; [ kuzu coreutils ];  # ← 依存を明示
  text = builtins.readFile ./src/kuzu-migrate.sh;
};
```

これにより：
1. **PATHの自動設定**: runtimeInputsがPATHに追加される
2. **純粋性の保証**: 外部環境に依存しない
3. **再現性**: どの環境でも同じ動作

## 4. 実証済みの外部使用パターン

### パターン1: CLIツールとして
```bash
# GitHub URLから直接実行
nix run "github:yourorg/kuzu-migration#kuzu-migrate" -- --help

# ローカルパスから実行
nix run "path:/path/to/kuzu-migration#kuzu-migrate" -- check
```

### パターン2: 依存パッケージとして
```nix
# 別プロジェクトのdevShell
devShells.default = pkgs.mkShell {
  packages = [
    kuzu-migration.packages.${system}.default
  ];
};
```

### パターン3: lib関数として
```nix
# カスタマイズされたマイグレーションツール
apps = kuzu-migration.lib.mkKuzuMigration {
  inherit pkgs;
  ddlPath = "./custom/migrations";
};
```

## 5. 推奨事項

### architecture/ddlチームへの実装推奨

1. **flake.nixの構成**
   ```nix
   {
     # packages: 実行可能ファイル
     packages.kuzu-ddl-tool = ...;
     
     # lib: 再利用可能な関数
     lib.mkDDLManager = { pkgs, config }: ...;
     
     # apps: 直接実行可能なコマンド
     apps.validate = ...;
   }
   ```

2. **テスト構造**
   ```
   tests/
   ├── unit/        # 単体テスト
   ├── integration/ # 統合テスト
   └── e2e/
       ├── internal/  # 内部E2E
       └── external/  # 外部使用テスト（必須）
   ```

3. **ドキュメント**
   ```markdown
   ## Installation
   # 直接実行
   nix run "github:yourorg/ddl-tool"
   
   # flake依存として追加
   inputs.ddl-tool.url = "github:yourorg/ddl-tool";
   ```

## 6. 担保のチェックリスト

外部使用が担保されているかの確認項目：

- [ ] `flake.nix`で`packages`/`lib`/`apps`を適切に公開
- [ ] `writeShellApplication`で依存関係を明示
- [ ] `tests/e2e/external/`に外部使用テストを実装
- [ ] 独立したflakeとしてテスト可能
- [ ] CIで外部テストを自動実行
- [ ] READMEに外部使用例を記載
- [ ] `nix flake check`がパスする

## まとめ

POCで実証した方法により、以下が担保されます：

1. **依存関係の完全性**: Nixが全依存を管理
2. **外部使用の検証**: external E2Eテストで確認
3. **使用方法の柔軟性**: CLI/package/lib関数として提供
4. **再現性**: どの環境でも同じ動作

この方法を採用することで、architecture/ddlチームのツールも外部プロジェクトから安心して使用できるようになります。