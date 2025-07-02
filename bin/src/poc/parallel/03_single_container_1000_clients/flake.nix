{
  description = "03 Single Container 1000 Clients - Extreme POC";

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
            htop  # リソース監視用
          ];

          shellHook = ''
            echo "🔥 POC 03: EXTREME - 1000 Clients Challenge"
            echo "=========================================="
            echo ""
            echo "⚠️  WARNING: This attempts 1000 concurrent connections!"
            echo ""
            echo "📋 Commands:"
            echo "  deno task start      - Start extreme server"
            echo "  deno task bench      - Run load test"
            echo "  deno task test:red   - Run failing tests"
            echo ""
            echo "🔧 System tuning recommended:"
            echo "  sudo sysctl -w net.core.somaxconn=4096"
            echo "  ulimit -n 65536"
            echo ""
          '';
        };
      });
}