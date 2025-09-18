{
  description = "Deno Runtime Permission POC - Minimal Infrastructure Security Control";

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
          ];

          shellHook = ''
            echo ">• Deno Runtime Permission POC Environment"
            echo "   Exploring minimal infrastructure security control"
            echo ""
            echo "Available commands:"
            echo "  deno run [flags] <script>  - Run with specific permissions"
            echo "  deno test                  - Run tests"
            echo "  deno fmt                   - Format code"
            echo "  deno lint                  - Lint code"
            echo ""
            echo "Permission flags examples:"
            echo "  --allow-read=./data        - Read access to ./data only"
            echo "  --allow-net=api.example.com - Network access to specific domain"
            echo "  --allow-env=API_KEY        - Access to specific env variable"
            echo ""
          '';
        };
      });
}