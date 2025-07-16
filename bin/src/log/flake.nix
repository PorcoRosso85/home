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
            deno
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
              # Run behavior tests
              export PYTHONPATH="$src:$PYTHONPATH"
              export PATH="${pkgs.deno}/bin:$PATH"
              pytest $src/test_behavior.py -v
            '';
          };
          
          default = self.packages.${system}.python;
        };
        
        # アプリケーション
        apps = {
          # 全言語振る舞いテスト（pytestのみ）
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-log" ''
              set -e
              echo "=== Running log API specification tests ==="
              cd /home/nixos/bin/src/log
              # DenoをPATHに追加
              export PATH="${pkgs.deno}/bin:$PATH"
              ${pythonEnv}/bin/pytest test_behavior.py -v
            ''}/bin/test-log";
          };
          
          default = self.apps.${system}.test;
        };
      });
}