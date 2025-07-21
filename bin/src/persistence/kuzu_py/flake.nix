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
          version = "0.1.0";
          
          src = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type: 
              (pkgs.lib.hasSuffix ".py" path) ||
              (pkgs.lib.hasSuffix "pyproject.toml" path) ||
              (pkgs.lib.hasSuffix "setup.py" path);
          };
          
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
        
        # テストランナー
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test" ''
              cd /home/nixos/bin/src/persistence/kuzu_py
              ${pythonEnv}/bin/pytest -v test_kuzu_py.py
            ''}/bin/test";
          };
          
          # e2eテストランナー
          e2e = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "e2e" ''
              cd /home/nixos/bin/src/persistence/kuzu_py
              echo "Running e2e tests for external import capability..."
              ${pythonEnv}/bin/pytest -v test_e2e.py
            ''}/bin/e2e";
          };
          
          # 全テスト実行
          test-all = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-all" ''
              cd /home/nixos/bin/src/persistence/kuzu_py
              echo "Running all tests..."
              ${pythonEnv}/bin/pytest -v test_kuzu_py.py test_e2e.py
            ''}/bin/test-all";
          };
        };
      });
}