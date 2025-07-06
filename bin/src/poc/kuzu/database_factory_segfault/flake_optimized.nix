{
  description = "POC for KuzuDB database factory segfault investigation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Approach 1: Pure Nix package override (理想的だが複雑)
        # kuzuパッケージを完全にオーバーライドして、
        # RPATHを適切に設定することでLD_LIBRARY_PATH不要に
        kuzuPatched = pkgs.python311Packages.kuzu.overrideAttrs (oldAttrs: {
          nativeBuildInputs = (oldAttrs.nativeBuildInputs or []) ++ [
            pkgs.autoPatchelfHook
          ];
          buildInputs = (oldAttrs.buildInputs or []) ++ [
            pkgs.stdenv.cc.cc.lib
          ];
          # 追加のパッチフェーズでRPATHを設定
          postFixup = (oldAttrs.postFixup or "") + ''
            # KuzuのSOファイルのRPATHを修正
            for lib in $out/lib/python*/site-packages/kuzu/*.so; do
              if [ -f "$lib" ]; then
                patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}:$(patchelf --print-rpath $lib)" "$lib"
              fi
            done
          '';
        });
        
        # Approach 2: シンプルだが内部でLD_LIBRARY_PATHを使用
        # (現在の実装)
        pythonEnvWrapped = pkgs.python311.withPackages (ps: with ps; [
          pytest
          kuzu
        ]);
        
        wrappedPythonEnv = pkgs.symlinkJoin {
          name = "python-kuzu-env";
          paths = [ pythonEnvWrapped ];
          buildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            for prog in $out/bin/*; do
              wrapProgram "$prog" \
                --set LD_LIBRARY_PATH "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}"
            done
          '';
        };
        
        # Approach 3: buildFHSEnv (完全な互換性環境)
        fhsEnv = pkgs.buildFHSEnv {
          name = "kuzu-fhs-env";
          targetPkgs = pkgs: with pkgs; [
            python311
            python311Packages.pytest
            python311Packages.kuzu
            stdenv.cc.cc.lib
          ];
        };
        
      in {
        # 開発シェル
        devShells = {
          # デフォルト: シンプルなラッパー方式
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              wrappedPythonEnv
              uv
              gcc
            ];
            
            shellHook = ''
              echo "KuzuDB Database Factory Segfault Investigation POC"
              echo "Using wrapped Python environment (LD_LIBRARY_PATH is handled internally)"
            '';
          };
          
          # 代替: パッチされたkuzuを使用（実験的）
          patched = pkgs.mkShell {
            buildInputs = with pkgs; [
              (python311.withPackages (ps: with ps; [
                pytest
                kuzuPatched
              ]))
              uv
              gcc
            ];
            
            shellHook = ''
              echo "KuzuDB POC - Using patched kuzu (no LD_LIBRARY_PATH needed)"
            '';
          };
          
          # 代替: FHS環境
          fhs = fhsEnv.env;
        };
        
        # アプリケーション
        apps = {
          # テスト実行（ラッパー方式）
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              PROJECT_DIR="/home/nixos/bin/src/poc/kuzu/database_factory_segfault"
              cd "$PROJECT_DIR"
              exec ${wrappedPythonEnv}/bin/pytest "$@"
            ''}";
          };
          
          # テスト実行（パッチ方式 - 実験的）
          test-patched = {
            type = "app";
            program = "${pkgs.writeShellScript "test-patched" ''
              PROJECT_DIR="/home/nixos/bin/src/poc/kuzu/database_factory_segfault"
              cd "$PROJECT_DIR"
              exec ${pkgs.python311.withPackages (ps: with ps; [pytest kuzuPatched])}/bin/pytest "$@"
            ''}";
          };
          
          # テスト実行（FHS方式）
          test-fhs = {
            type = "app";
            program = "${pkgs.writeShellScript "test-fhs" ''
              PROJECT_DIR="/home/nixos/bin/src/poc/kuzu/database_factory_segfault"
              cd "$PROJECT_DIR"
              exec ${fhsEnv}/bin/kuzu-fhs-env pytest "$@"
            ''}";
          };
          
          # デフォルト
          default = self.apps.${system}.test;
        };
      });
}