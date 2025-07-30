{
  description = "graph_docs POC - Dual KuzuDB Query Interface";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pytest
          pytest-asyncio
          kuzu
          typer
          rich
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
                ×í¸§¯È: graph_docs POC
                
                ¬Ù: 2dnKuzuDBÇ£ì¯ÈêkþY‹B¯¨êhêìü·çóš©
                
                )(ïýj³ÞóÉ:
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