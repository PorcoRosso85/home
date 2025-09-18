{
  description = "PGlite WASM assets as Nix derivation";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        engine = "pglite";
        version = "0.2.12";
      in
      {
        packages = {
          assets = pkgs.stdenv.mkDerivation {
            pname = "wasm-${engine}-assets";
            inherit version;
            
            src = pkgs.fetchurl {
              url = "https://registry.npmjs.org/@electric-sql/pglite/-/@electric-sql/pglite-${version}.tgz";
              sha256 = "0i40lm4dwijipyci8hsj912rf2w7jsnci7rir6mlsd1l50grw68s";
            };
            
            buildCommand = ''
              mkdir -p $out/wasm/${engine}
              tar -xzf $src
              
              # Extract WASM files and essential assets
              cp package/dist/postgres.wasm $out/wasm/${engine}/
              cp package/dist/postgres.data $out/wasm/${engine}/
              cp package/dist/postgres.js $out/wasm/${engine}/
              
              # Copy core JavaScript files
              cp package/dist/index.js $out/wasm/${engine}/
              cp package/dist/*.js $out/wasm/${engine}/ 2>/dev/null || true
              
              # Create manifest file
              cat > $out/wasm/${engine}/manifest.json << EOF
              {
                "engine": "${engine}",
                "version": "${version}",
                "files": {
                  "wasm": "postgres.wasm",
                  "data": "postgres.data",
                  "js": "postgres.js",
                  "entry": "index.js"
                }
              }
              EOF
            '';
          };
          
          default = self.packages.${system}.assets;
        };
        
        checks = {
          selftest = pkgs.runCommand "test-${engine}" {} ''
            # Verify essential PGlite WASM files exist
            assets=${self.packages.${system}.assets}
            
            echo "Checking PGlite WASM assets..."
            
            # Check core files
            [ -f "$assets/wasm/${engine}/postgres.wasm" ] || (echo "Missing postgres.wasm" && exit 1)
            [ -f "$assets/wasm/${engine}/postgres.data" ] || (echo "Missing postgres.data" && exit 1)
            [ -f "$assets/wasm/${engine}/postgres.js" ] || (echo "Missing postgres.js" && exit 1)
            [ -f "$assets/wasm/${engine}/index.js" ] || (echo "Missing index.js" && exit 1)
            [ -f "$assets/wasm/${engine}/manifest.json" ] || (echo "Missing manifest.json" && exit 1)
            
            # Verify WASM file is binary
            file "$assets/wasm/${engine}/postgres.wasm" | grep -q "WebAssembly" || (echo "Invalid WASM format" && exit 1)
            
            # Verify manifest has correct structure
            ${pkgs.jq}/bin/jq -e '.engine == "${engine}" and .version == "${version}"' "$assets/wasm/${engine}/manifest.json" > /dev/null || (echo "Invalid manifest" && exit 1)
            
            echo "All PGlite WASM assets verified successfully"
            touch $out
          '';
        };
      });
}