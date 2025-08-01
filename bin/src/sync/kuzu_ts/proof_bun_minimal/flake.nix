{
  description = "Minimal Bun client with only persistence/kuzu_ts dependency";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # ONLY dependency: persistence/kuzu_ts
    kuzu-ts.url = "path:../../../persistence/kuzu_ts";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # Get Bun-specific package from persistence/kuzu_ts
        kuzuTsBunPackage = kuzu-ts.packages.${system}.bun;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Bun from nixpkgs - NO additional input needed
            bun
            # System libraries for native modules
            stdenv.cc.cc.lib
          ];
          
          shellHook = ''
            echo "🎯 Minimal Bun + persistence/kuzu_ts Environment"
            echo "=============================================="
            echo ""
            echo "✅ Bun provided by: nixpkgs (no flake.input needed)"
            echo "✅ KuzuDB provided by: persistence/kuzu_ts (only flake.input)"
            echo ""
            
            # Set up LD_LIBRARY_PATH for native modules
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Link persistence/kuzu_ts package
            if [ ! -d node_modules ]; then
              echo "📦 Setting up node_modules..."
              mkdir -p node_modules
              ln -sf ${kuzuTsBunPackage}/lib/node_modules/kuzu node_modules/kuzu
              echo "✅ Linked kuzu from persistence/kuzu_ts"
            fi
            
            echo ""
            echo "🚀 Ready! No additional configuration needed."
          '';
        };
        
        # Minimal app to prove it works
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "test-minimal" ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Ensure node_modules link exists
            if [ ! -d node_modules ]; then
              mkdir -p node_modules
              ln -sf ${kuzuTsBunPackage}/lib/node_modules/kuzu node_modules/kuzu
            fi
            
            echo "🧪 Running minimal test..."
            exec ${pkgs.bun}/bin/bun run test.js
          ''}";
        };
      });
}