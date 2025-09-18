{
  description = "Event Sourcing POC with KuzuDB WASM";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Node modules with KuzuDB WASM
        nodeModules = pkgs.stdenv.mkDerivation {
          name = "node-modules";
          src = ./.;
          buildInputs = with pkgs; [ nodejs_20 ];
          buildPhase = ''
            export HOME=$TMP
            npm install --package-lock-only
            npm ci
          '';
          installPhase = ''
            mkdir -p $out
            cp -r node_modules $out/
          '';
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
            nodePackages.npm
          ];

          shellHook = ''
            echo "🚀 Event Sourcing POC with KuzuDB WASM"
            echo "===================================="
            echo "Deno ${pkgs.deno.version} | Node.js ${pkgs.nodejs_20.version}"
            echo ""
            
            # Setup node_modules if not exists
            if [ ! -d "node_modules" ]; then
              echo "Installing KuzuDB WASM..."
              npm install
            fi
            
            echo "Tests: npm test"
          '';
        };
      });
}