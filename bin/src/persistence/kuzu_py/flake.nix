{
  description = "KuzuDB thin wrapper for Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # カスタマイズ可能なkuzuパッケージ
        customKuzu = pkgs.python312Packages.kuzu.overrideAttrs (oldAttrs: {
          # 拡張機能をここで追加可能
        });
        
        # kuzu_py パッケージ  
        kuzuPy = pkgs.python312Packages.buildPythonPackage rec {
          pname = "kuzu_py";
          version = "0.1.1";
          
          # Use simple source for now
          src = ./.;
          
          # setuptools形式でビルド
          pyproject = true;
          build-system = with pkgs.python312Packages; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            customKuzu
          ];
          
          pythonImportsCheck = [ "kuzu_py" ];
          doCheck = false;
        };
        
        # Python環境
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          kuzuPy
          pytest
        ]);
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
          
          shellHook = ''
            echo "KuzuDB thin wrapper"
            echo "Python version: $(python --version)"
          '';
        };
        
        # パッケージ出力
        packages = {
          default = pythonEnv;
          kuzu = customKuzu;
          pythonEnv = pythonEnv;
          kuzuPy = kuzuPy;
        };
        
        # テストランナー（規約準拠）
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test" ''
              cd /home/nixos/bin/src/persistence/kuzu_py
              
              # ユニット・統合テスト
              ${pythonEnv}/bin/pytest -v test_kuzu_py.py test_query_loader.py
              
              # 内部E2Eテスト
              if [ -d "e2e/internal" ]; then
                ${pythonEnv}/bin/pytest -v e2e/internal/
              fi
              
              # 外部E2Eテスト
              if [ -f "e2e/external/flake.nix" ]; then
                (cd e2e/external && nix run .#test)
              fi
            ''}/bin/test";
          };
          
          # 全テスト実行（規約準拠）
          test-all = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-all" ''
              cd /home/nixos/bin/src/persistence/kuzu_py
              echo "Running all tests..."
              
              # ユニット・統合テスト
              ${pythonEnv}/bin/pytest -v test_kuzu_py.py test_query_loader.py
              
              # 内部E2Eテスト
              if [ -d "e2e/internal" ]; then
                ${pythonEnv}/bin/pytest -v e2e/internal/
              fi
              
              # 外部E2Eテスト
              if [ -f "e2e/external/flake.nix" ]; then
                echo "Running external E2E tests..."
                (cd e2e/external && nix run .#test)
              fi
            ''}/bin/test-all";
          };
          
          # query loaderテストランナー
          test-query-loader = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-query-loader" ''
              cd /home/nixos/bin/src/persistence/kuzu_py
              echo "Running query loader tests..."
              ${pythonEnv}/bin/pytest -v test_query_loader.py
            ''}/bin/test-query-loader";
          };
        };
      });
}