{
  description = "POC 11: Dual Servers Manual Split";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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
            docker
            docker-compose
            postgresql
            nginx
            curl
            jq
          ];

          shellHook = ''
            echo "🚀 POC 11: Dual Servers Manual Split"
            echo "=================================="
            echo ""
            echo "📋 Available commands:"
            echo "  deno task test       - Run tests"
            echo "  deno task server1    - Start server 1 (A-M)"
            echo "  deno task server2    - Start server 2 (N-Z)"
            echo ""
            echo "🔧 Test commands:"
            echo "  nix develop -c deno task test"
            echo ""
            echo "📚 Documentation:"
            echo "  See README.md for detailed setup"
            echo ""
          '';
        };
      });
}