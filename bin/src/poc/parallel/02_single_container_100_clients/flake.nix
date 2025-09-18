{
  description = "02 Single Container 100 Clients POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
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
            deno
            curl
          ];

          shellHook = ''
            echo "🚀 POC 02: Single Container 100 Clients"
            echo "======================================="
            echo ""
            echo "📋 Quick start:"
            echo "  deno task start      - Start server"
            echo "  deno task test       - Run tests"  
            echo "  deno task load-test  - Run load test (100 clients)"
            echo ""
          '';
        };
      });
}