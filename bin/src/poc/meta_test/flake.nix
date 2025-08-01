{
  description = "Meta-test system for evaluating test quality with 7 independent metrics";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu_py.url = "path:../../persistence/kuzu_py";
    python-flake.url = "path:../../flakes/python";
  };
  
  outputs = { self, nixpkgs, flake-utils, kuzu_py, python-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Import kuzu_py package from persistence/kuzu_py
        kuzuPyPkg = kuzu_py.packages.${system}.kuzuPy;
        
        # Meta-test package - using direct Python environment without separate package build
        metaTestDeps = with pkgs.python312Packages; [
          # Domain dependencies
          pydantic
          numpy
          
          # Infrastructure dependencies
          httpx
          aiofiles
          # KuzuDB is now provided through kuzu_py package
          
          # Testing dependencies
          pytest
          pytest-asyncio
          pytest-cov
        ];
        
        # Python環境
        pythonEnv = pkgs.python312.withPackages (ps: 
          [kuzuPyPkg] ++ metaTestDeps ++ (with ps; [
            # Additional dev tools
            ruff
          ])
        );
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            python-flake.packages.${system}.pyright
          ];
          
          shellHook = ''
            echo "Meta-test system for evaluating test quality"
            echo "Python version: $(python --version)"
            export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
          '';
        };
        
        # パッケージ出力
        packages = {
          default = pythonEnv;
          pythonEnv = pythonEnv;
        };
        
        # テストランナー（規約準拠）
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              
              # ユニット・統合テスト (project structure uses test_*.py pattern)
              ${pythonEnv}/bin/pytest -v domain/ application/ infrastructure/
              
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
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              echo "Running all tests..."
              
              # ユニット・統合テスト (project structure uses test_*.py pattern)
              ${pythonEnv}/bin/pytest -v domain/ application/ infrastructure/
              
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
          
          # Development tools
          format = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "format" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/ruff format . "$@"
            ''}/bin/format";
          };
          
          lint = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "lint" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/ruff check . "$@"
            ''}/bin/lint";
          };
          
          
          pyright = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "pyright" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${python-flake.packages.${system}.pyright}/bin/pyright "$@"
            ''}/bin/pyright";
          };
          
          # Meta-test specific commands
          init = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "init" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/python -m meta_test init "$@"
            ''}/bin/init";
          };
          
          calculate = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "calculate" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/python -m meta_test calculate "$@"
            ''}/bin/calculate";
          };
          
          check = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "check" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/python -m meta_test check "$@"
            ''}/bin/check";
          };
          
          suggest = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "suggest" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/python -m meta_test suggest "$@"
            ''}/bin/suggest";
          };
          
          learn = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "learn" ''
              cd /home/nixos/bin/src/poc/meta_test
              export PYTHONPATH="/home/nixos/bin/src/poc/meta_test:$PYTHONPATH"
              ${pythonEnv}/bin/python -m meta_test learn "$@"
            ''}/bin/learn";
          };
        };
      });
}