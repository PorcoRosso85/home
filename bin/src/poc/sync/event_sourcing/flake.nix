{
  description = "Template-based Event Sourcing POC with Deno";

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
            jq  # JSON処理用
          ];

          shellHook = ''
            echo "🚀 Template-based Event Sourcing POC"
            echo "===================================="
            echo ""
            echo "📋 Available commands:"
            echo "  deno task test       - Run TDD Red phase tests"
            echo "  deno task test:watch - Run tests in watch mode"
            echo "  deno task coverage   - Run tests with coverage"
            echo ""
            echo "📁 Template files:"
            ls -la templates/*.cypher 2>/dev/null | wc -l | xargs -I {} echo "  {} Cypher templates found"
            echo ""
            echo "🔴 TDD Red Phase: All tests should fail initially"
          '';
        };
      });
}