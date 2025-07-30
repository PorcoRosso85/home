{
  description = "Test using packaged kuzu_ts";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu-ts.url = "path:../..";
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        kuzuTsPackage = kuzu-ts.packages.${system}.default;
      in
      {
        # Test script
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "test-kuzu-ts" ''
            set -e
            
            echo "Testing packaged kuzu_ts..."
            echo "Package location: ${kuzuTsPackage}"
            
            # Create a test script
            cat > test.ts <<EOF
            import { KUZU_VERSION } from "${kuzuTsPackage}/lib/kuzu_ts/mod_worker.ts";
            console.log("KuzuDB version from package:", KUZU_VERSION);
            
            // Test that we can import from the package
            import { KuzuTsDatabase } from "${kuzuTsPackage}/lib/kuzu_ts/core/database.ts";
            console.log("Successfully imported KuzuTsDatabase!");
            EOF
            
            # Set up environment
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export NODE_PATH="${kuzuTsPackage}/lib/node_modules:$NODE_PATH"
            
            # Run the test
            ${pkgs.deno}/bin/deno run --allow-all --unstable-ffi test.ts
            
            echo "✅ Test passed! Package is working correctly."
          ''}";
        };
      });
}