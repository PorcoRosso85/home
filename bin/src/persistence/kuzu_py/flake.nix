{
  description = "KuzuDB thin wrapper for Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      # システム非依存の出力
      lib = {
        pythonPath = ./.;
        moduleImport = "kuzu_py";
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # カスタマイズ可能なkuzuパッケージ
        customKuzu = pkgs.python312Packages.kuzu.overrideAttrs (oldAttrs: {
          # 拡張機能をここで追加可能
        });
        
        # Python環境
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          customKuzu
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
            export PYTHONPATH="$PWD/..:$PYTHONPATH"
            echo "KuzuDB thin wrapper"
            echo "Python version: $(python --version)"
          '';
        };
        
        # パッケージ出力
        packages = {
          default = pythonEnv;
          kuzu = customKuzu;
          pythonEnv = pythonEnv;
        };
        
        # テストランナー
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test" ''
            export PYTHONPATH="/home/nixos/bin/src/persistence:$PYTHONPATH"
            cd /home/nixos/bin/src/persistence/kuzu_py
            ${pythonEnv}/bin/pytest -v test_kuzu_py.py
          ''}/bin/test";
        };
      });
}