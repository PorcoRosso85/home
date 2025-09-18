{
  description = "Official SQLite WASM assets as Nix derivation";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        engine = "sqlite";
        version = "3.50.4-build1";
      in
      {
        packages = {
          assets = pkgs.stdenv.mkDerivation {
            pname = "wasm-${engine}-assets";
            inherit version;
            
            src = pkgs.fetchurl {
              url = "https://registry.npmjs.org/@sqlite.org/sqlite-wasm/-/sqlite-wasm-${version}.tgz";
              sha256 = "0wgarg51rd5xhla1003r0zvdq31wwwbh7df9x9bxkw2gyn5cc0rw";
            };
            
            buildCommand = ''
              mkdir -p $out/wasm/${engine}
              tar -xzf $src
              
              # Extract from package/sqlite-wasm/jswasm/
              cp package/sqlite-wasm/jswasm/sqlite3.wasm $out/wasm/${engine}/
              cp package/sqlite-wasm/jswasm/sqlite3.js $out/wasm/${engine}/
              cp package/sqlite-wasm/jswasm/sqlite3.mjs $out/wasm/${engine}/
              
              # Worker versions
              cp package/sqlite-wasm/jswasm/sqlite3-worker1.js $out/wasm/${engine}/
              cp package/sqlite-wasm/jswasm/sqlite3-worker1-bundler-friendly.mjs $out/wasm/${engine}/
              cp package/sqlite-wasm/jswasm/sqlite3-worker1-promiser.js $out/wasm/${engine}/
              cp package/sqlite-wasm/jswasm/sqlite3-worker1-promiser.mjs $out/wasm/${engine}/
              
              # OPFS proxy
              cp package/sqlite-wasm/jswasm/sqlite3-opfs-async-proxy.js $out/wasm/${engine}/
              
              # Node.js version (optional)
              cp package/sqlite-wasm/jswasm/sqlite3-node.mjs $out/wasm/${engine}/ || true
              
              # List all files for verification
              ls -la $out/wasm/${engine}/ > $out/wasm/${engine}/files.txt
            '';
          };
          
          default = self.packages.${system}.assets;
        };
        
        checks = {
          selftest = pkgs.runCommand "test-${engine}" {} ''
            # Verify essential files exist
            test -e ${self.packages.${system}.assets}/wasm/${engine}/sqlite3.wasm
            test -e ${self.packages.${system}.assets}/wasm/${engine}/sqlite3.js
            test -e ${self.packages.${system}.assets}/wasm/${engine}/sqlite3.mjs
            
            # Verify worker files
            test -e ${self.packages.${system}.assets}/wasm/${engine}/sqlite3-worker1.js
            test -e ${self.packages.${system}.assets}/wasm/${engine}/sqlite3-worker1-bundler-friendly.mjs
            
            # Verify WASM file format (magic bytes check)
            ${pkgs.hexdump}/bin/hexdump -n 4 ${self.packages.${system}.assets}/wasm/${engine}/sqlite3.wasm | grep -q "0000000 6100 6d73" || (echo "Not a valid WASM file" && exit 1)
            
            # Check file size (should be > 100KB)
            size=$(stat -c%s ${self.packages.${system}.assets}/wasm/${engine}/sqlite3.wasm)
            if [ $size -lt 100000 ]; then
              echo "WASM file too small: $size bytes"
              exit 1
            fi
            
            echo "SQLite Official WASM assets validation successful" > $out
          '';
        };
      });
}