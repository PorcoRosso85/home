{
  description = "Universal log API specification";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pytest
        ]);
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            nodejs_20
            go
            bash
            jq
          ];
          
          shellHook = ''
            echo "Log API development environment"
            echo "Available languages: Python, JavaScript, Go, Shell"
            echo "Run tests: nix run .#test"
          '';
        };
        
        # パッケージ
        packages = {
          # Python実装
          python = pkgs.python3Packages.buildPythonPackage {
            pname = "log";
            version = "0.1.0";
            src = ./.;
            format = "other";
            
            propagatedBuildInputs = [];
            
            checkInputs = [ pkgs.python3Packages.pytest ];
            
            installPhase = ''
              mkdir -p $out/lib/python3.*/site-packages/log
              cp *.py $out/lib/python3.*/site-packages/log/
            '';
            
            checkPhase = ''
              # Run tests in the source directory
              export PYTHONPATH="$src:$PYTHONPATH"
              pytest $src/test_log.py -v
            '';
          };
          
          default = self.packages.${system}.python;
        };
        
        # アプリケーション
        apps = {
          # テスト実行
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-log" ''
              set -e
              echo "=== Running log module tests ==="
              cd /home/nixos/bin/src/log
              PYTHONPATH=. ${pythonEnv}/bin/pytest test_log.py -v
            ''}/bin/test-log";
          };
          
          # 出力例の実行
          example = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "log-example" ''
              cd ${./.}
              ${pythonEnv}/bin/python test_output.py
            ''}/bin/log-example";
          };
          
          default = self.apps.${system}.test;
        };
      });
}