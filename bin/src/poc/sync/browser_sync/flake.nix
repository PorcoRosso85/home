{
  description = "Browser Sync POC";

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
            echo "Browser Sync POC - Development Environment"
            echo ""
            echo "Commands:"
            echo "  deno task dev   - Start server with auto-reload"
            echo "  deno task start - Start server"
            echo ""
            echo "Open http://localhost:8080 in multiple browsers to test"
          '';
        };
      });
}