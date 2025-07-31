{
  description = "Test external project using kuzu-ts Bun package";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../..";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        kuzu-bun = kuzu-ts.packages.${system}.bun;
      in
      {
        # Test application that uses the kuzu-ts Bun package
        packages.test = pkgs.writeShellScriptBin "test-kuzu-bun" ''
          echo "Testing kuzu-ts Bun package from external project..."
          echo "================================================="
          
          # Set up environment
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          export KUZU_TS_PATH="${kuzu-bun}/lib/kuzu_ts_bun"
          export NODE_PATH="${kuzu-bun}/lib/node_modules:$NODE_PATH"
          
          # Copy test file to temp directory to test isolation
          TEMP_DIR=$(mktemp -d)
          cp ${./test.ts} $TEMP_DIR/test.ts
          cd $TEMP_DIR
          
          # Create a simple package.json to help with module resolution
          cat > package.json <<EOF
          {
            "name": "test-kuzu-bun",
            "type": "module",
            "dependencies": {}
          }
          EOF
          
          # Link node_modules from the package
          ln -s ${kuzu-bun}/lib/node_modules/kuzu_ts/node_modules node_modules
          
          # Debug: Show what's available
          echo "Package contents:"
          ls -la ${kuzu-bun}/lib/kuzu_ts_bun/ || true
          echo ""
          echo "Node modules:"
          ls -la ${kuzu-bun}/lib/node_modules/ || true
          echo ""
          
          # Run test with Bun from the packaged version
          ${pkgs.bun}/bin/bun run test.ts
          
          # Clean up
          cd ..
          rm -rf $TEMP_DIR
        '';
        
        # Default package
        packages.default = self.packages.${system}.test;
        
        # Development shell for debugging
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            bun
            stdenv.cc.cc.lib
          ];
          
          shellHook = ''
            echo "Test environment for kuzu-ts Bun package"
            echo "Bun version: $(bun --version)"
            echo ""
            echo "Kuzu-ts Bun package location: ${kuzu-bun}"
            echo "Run 'nix run' to execute the test"
            
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="${kuzu-bun}/lib/kuzu_ts_bun"
          '';
        };
        
        # App to run the test
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.test}/bin/test-kuzu-bun";
        };
      });
}