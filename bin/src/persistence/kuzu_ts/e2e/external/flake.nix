{
  description = "External E2E test for kuzu_ts - Tests cross-project usage";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../..";  # Target package to test
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Test app that verifies external usage
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test-external" ''
            set -e
            
            echo "🧪 Testing kuzu_ts as external package"
            echo "======================================"
            
            # Set up environment
            export PATH="${pkgs.deno}/bin:$PATH"
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Install npm:kuzu for Worker support (as documented in CROSS_PROJECT_SOLUTION.md)
            echo "📦 Installing npm:kuzu@0.10.0 for Worker support..."
            # NOTE: In a real project, you could dynamically determine the version:
            # - Import KUZU_VERSION from the kuzu_ts module
            # - Use it to ensure compatibility with the wrapped library
            # - Example: npm:kuzu@''${KUZU_VERSION} (if versions align)
            # For now, we use a fixed version that matches our requirements
            ${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@0.10.0
            
            # Patch native modules
            for lib in node_modules/.deno/*/node_modules/kuzu/*.node; do
              [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib" || true
            done
            
            # Run the test
            echo "🚀 Running external import test..."
            ${pkgs.deno}/bin/deno test \
              --allow-all \
              --unstable-worker-options \
              test_e2e_import.ts
            
            echo "✅ External package test completed!"
          ''}/bin/test-external";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
            stdenv.cc.cc.lib
            patchelf
          ];
          
          shellHook = ''
            echo "External E2E Test Environment for kuzu_ts"
            echo "Run: nix run .#test"
          '';
        };
      });
}