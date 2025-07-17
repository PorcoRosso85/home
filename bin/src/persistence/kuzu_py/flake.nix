{
  description = "KuzuDB Python persistence layer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      # システム非依存の出力
      lib = {
        pythonPath = ./.;
        moduleImport = "core.database";
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
          numpy
          pandas
          pytest
          pydantic
        ]);
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
          
          shellHook = ''
            export PYTHONPATH="$PWD:$PYTHONPATH"
            echo "KuzuDB Python persistence layer"
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
            cd ${../.}
            export PYTHONPATH="${./.}:$PYTHONPATH"
            ${pythonEnv}/bin/python test_minimal_kuzu.py
          ''}/bin/test";
        };
      });
}