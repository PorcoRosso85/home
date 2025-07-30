{
  description = "graph_docs POC - Dual KuzuDB Query Interface";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    python-flake.url = "path:/home/nixos/bin/src/flakes/python";
    kuzu-py-flake.url = "path:/home/nixos/bin/src/persistence/kuzu_py";
  };

  outputs = { self, nixpkgs, flake-utils, python-flake, kuzu-py-flake, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # 親flakeからPythonバージョンを継承し、追加パッケージを含めて再構築
        basePython = python-flake.packages.${system}.pythonEnv.python;
        pythonEnv = basePython.withPackages (ps: with ps; [
          pytest
          pytest-asyncio
          kuzu  # nixpkgsのkuzuを使用
        ]);

      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "graph-docs";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pythonEnv ];
          
          installPhase = ''
            mkdir -p $out/bin
            cp mod.py $out/
            cp main.py $out/bin/graph-docs
            chmod +x $out/bin/graph-docs
            
            # Add shebang and module path
            sed -i '1i#!/usr/bin/env python3' $out/bin/graph-docs
            sed -i '2iimport sys; sys.path.insert(0, "'$out'")' $out/bin/graph-docs
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
        };

        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                プロジェクト: graph_docs POC
                
                責務: 2つのKuzuDBディレクトリに対する同時クエリとリレーション定義
                
                利用可能なコマンド:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${./.}
              exec ${pythonEnv}/bin/pytest -v
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              cat ${./README.md}
            ''}";
          };

          query = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/graph-docs";
          };
        };
      }
    );
}