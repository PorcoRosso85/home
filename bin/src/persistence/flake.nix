{
  description = "Persistence layer with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        
        # カスタマイズ可能なkuzuパッケージ
        customKuzu = pkgs.python312Packages.kuzu.overrideAttrs (oldAttrs: {
          # ここで拡張機能や設定を追加可能
          # 例: postInstall = oldAttrs.postInstall or "" + ''
          #   echo "Custom kuzu extensions installed"
          # '';
        });
        
        # 基本的なPython環境
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          customKuzu
          numpy
          pandas
          pytest
          pytest-asyncio
          pydantic
        ]);
        
        # persistenceモジュール付きPython環境
        pythonWithPersistence = pkgs.python312.withPackages (ps: with ps; [
          customKuzu
          numpy
          pandas
          pydantic
        ] ++ [(pkgs.python312.pkgs.buildPythonPackage {
          pname = "persistence-kuzu";
          version = "0.1.0";
          src = ./.;
          propagatedBuildInputs = with ps; [
            customKuzu
            numpy
            pandas
            pydantic
          ];
          # テストを無効化（循環依存を避けるため）
          doCheck = false;
        })]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
          
          shellHook = ''
            echo "Persistence layer development environment"
            echo "Python version: $(python --version)"
            echo "Using Nix-provided kuzu package only"
          '';
        };
        
        # 外部から直接参照するための出力
        lib = {
          # PYTHONPATHに追加するディレクトリ
          pythonPath = ./.;
          
          # shellHookで使用可能な環境変数設定
          shellHook = ''
            export PYTHONPATH="${./.}:$PYTHONPATH"
          '';
        };
        
        packages = {
          default = pythonEnv;
          
          # カスタマイズされたkuzuのみ
          kuzu = customKuzu;
          
          # persistenceモジュール付きPython環境
          pythonWithPersistence = pythonWithPersistence;
          
          # persistenceモジュールのみ（他のプロジェクトから利用可能）
          persistenceModule = pkgs.python312.pkgs.buildPythonPackage {
            pname = "persistence-kuzu";
            version = "0.1.0";
            src = ./.;
            propagatedBuildInputs = with pkgs.python312Packages; [
              customKuzu
              numpy
              pandas
              pydantic
            ];
            doCheck = false;
          };
        };
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test" ''
            export PYTHONPATH="$PWD:$PYTHONPATH"
            ${pythonEnv}/bin/python test_minimal_kuzu.py
          ''}/bin/test";
        };
      });
}