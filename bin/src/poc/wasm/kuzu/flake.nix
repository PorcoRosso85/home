{
  description = "Kuzu WASM assets as Nix derivation";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        engine = "kuzu";
        version = "1.0.4";
      in
      {
        packages = {
          assets = pkgs.stdenv.mkDerivation {
            pname = "wasm-${engine}-assets";
            inherit version;
            
            src = pkgs.fetchurl {
              url = "https://registry.npmjs.org/@kuzu/kuzu-wasm/-/kuzu-wasm-${version}.tgz";
              sha256 = "0igvp82lajk3kkzllm8fp2rj0738qwrxibycf33v43q7n7sg9vl6";
            };
            
            buildCommand = ''
              mkdir -p $out/wasm/${engine}
              tar -xzf $src
              
              # Extract and copy WASM files from package/dist/
              cd package/dist
              cp kuzu-wasm.wasm $out/wasm/${engine}/
              cp kuzu.js $out/wasm/${engine}/
              cp kuzu-wasm.js $out/wasm/${engine}/
              cp kuzu-wasm.worker.mjs $out/wasm/${engine}/
              
              # Create index file listing available files
              echo "kuzu-wasm.wasm" > $out/wasm/${engine}/files.txt
              echo "kuzu.js" >> $out/wasm/${engine}/files.txt
              echo "kuzu-wasm.js" >> $out/wasm/${engine}/files.txt
              echo "kuzu-wasm.worker.mjs" >> $out/wasm/${engine}/files.txt
            '';
          };
          
          default = self.packages.${system}.assets;
        };
        
        checks = {
          selftest = pkgs.runCommand "test-${engine}" {} ''
            # Verify that all expected WASM files exist
            assets=${self.packages.${system}.assets}
            
            echo "Checking for kuzu WASM assets in $assets/wasm/${engine}/"
            
            # Check WASM binary
            if [ ! -f "$assets/wasm/${engine}/kuzu-wasm.wasm" ]; then
              echo "ERROR: kuzu-wasm.wasm not found"
              exit 1
            fi
            echo "✓ kuzu-wasm.wasm found"
            
            # Check JavaScript files
            if [ ! -f "$assets/wasm/${engine}/kuzu.js" ]; then
              echo "ERROR: kuzu.js not found"
              exit 1
            fi
            echo "✓ kuzu.js found"
            
            if [ ! -f "$assets/wasm/${engine}/kuzu-wasm.js" ]; then
              echo "ERROR: kuzu-wasm.js not found"
              exit 1
            fi
            echo "✓ kuzu-wasm.js found"
            
            # Check worker file
            if [ ! -f "$assets/wasm/${engine}/kuzu-wasm.worker.mjs" ]; then
              echo "ERROR: kuzu-wasm.worker.mjs not found"
              exit 1
            fi
            echo "✓ kuzu-wasm.worker.mjs found"
            
            # Check files index
            if [ ! -f "$assets/wasm/${engine}/files.txt" ]; then
              echo "ERROR: files.txt index not found"
              exit 1
            fi
            echo "✓ files.txt index found"
            
            # Verify file sizes are reasonable
            wasm_size=$(stat -c%s "$assets/wasm/${engine}/kuzu-wasm.wasm")
            if [ "$wasm_size" -lt 100000 ]; then
              echo "ERROR: WASM file too small ($wasm_size bytes), may be corrupted"
              exit 1
            fi
            echo "✓ WASM file size reasonable: $wasm_size bytes"
            
            echo "All kuzu WASM assets verified successfully"
            touch $out
          '';
        };
      });
}