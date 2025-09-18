{
  description = "DuckDB WASM assets as Nix derivation";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        engine = "duckdb";
        version = "1.28.1-dev106.0";
      in
      {
        packages = {
          assets = pkgs.stdenv.mkDerivation {
            pname = "wasm-${engine}-assets";
            inherit version;
            
            src = pkgs.fetchurl {
              url = "https://registry.npmjs.org/@duckdb/duckdb-wasm/-/duckdb-wasm-${version}.tgz";
              sha256 = "0w57sv4hjlvy1f5ch0yf90j9al8k4mgapkddvsh5n08b4564b1gb";
            };
            
            buildCommand = ''
              mkdir -p $out/wasm/${engine}
              tar -xzf $src
              
              # Copy WASM files
              cp package/dist/duckdb-mvp.wasm $out/wasm/${engine}/
              cp package/dist/duckdb-eh.wasm $out/wasm/${engine}/
              cp package/dist/duckdb-coi.wasm $out/wasm/${engine}/
              
              # Copy worker files
              cp package/dist/*.worker.js $out/wasm/${engine}/
              
              # Copy JS files (CommonJS, ES modules, and browser JS)
              cp package/dist/duckdb*.js $out/wasm/${engine}/
              cp package/dist/duckdb*.cjs $out/wasm/${engine}/
              cp package/dist/duckdb*.mjs $out/wasm/${engine}/
            '';
          };
          
          default = self.packages.${system}.assets;
        };
        
        checks = {
          selftest = pkgs.runCommand "test-${engine}" {} ''
            # Verify WASM files exist
            test -e ${self.packages.${system}.assets}/wasm/${engine}/duckdb-mvp.wasm
            test -e ${self.packages.${system}.assets}/wasm/${engine}/duckdb-eh.wasm
            
            # Verify worker files exist
            test -e ${self.packages.${system}.assets}/wasm/${engine}/duckdb-browser-mvp.worker.js
            test -e ${self.packages.${system}.assets}/wasm/${engine}/duckdb-browser-eh.worker.js
            
            # Output success
            echo "DuckDB WASM assets validation successful" > $out
          '';
        };
      });
}