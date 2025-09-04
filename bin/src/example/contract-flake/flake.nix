{
  description = "Flake contract system - TypeScript-based contract definitions for Nix flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            bun
            nodePackages.typescript
            nodePackages.typescript-language-server
          ];

          shellHook = ''
            echo "Flake Contract System Development Environment"
            echo "============================================"
            echo "Bun: $(bun --version)"
            echo ""
            echo "Available commands:"
            echo "  bun run type-check - Type check all TypeScript files"
            echo "  bun test           - Run tests"
            echo "  bun run format     - Format code"
            echo "  bun run start      - Run the application"
            echo ""
          '';
        };

        # Flake contract metadata (consumed by glue system)
        contract = {
          version = "0.1.0";
          interface = {
            inputs = {
              nixpkgs = "flake:nixpkgs";
              flake-utils = "flake:flake-utils";
            };
            outputs = {
              devShell = "derivation";
              contract = "attrset";
            };
          };
          capabilities = [ "bun" "typescript" "glue" ];
        };

        # Package definition for the contract system
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "flake-contract";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pkgs.bun ];
          
          buildPhase = ''
            bun install --production
          '';
          
          installPhase = ''
            mkdir -p $out/bin $out/lib
            cp -r src $out/lib/
            cp package.json $out/lib/
            cat > $out/bin/flake-contract <<EOF
            #!/usr/bin/env bash
            exec ${pkgs.bun}/bin/bun run $out/lib/src/glue/flake-glue.ts "\$@"
            EOF
            chmod +x $out/bin/flake-contract
          '';
        };
      });
}