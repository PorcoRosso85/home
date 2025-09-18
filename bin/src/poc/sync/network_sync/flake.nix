{
  description = "Network Sync POC - Deno Implementation";

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
            echo "Network Sync POC - Deno Implementation"
            echo ""
            echo "Commands:"
            echo "  deno task test       - Run network sync tests"
            echo "  deno task test:watch - Run tests in watch mode"
            echo ""
            echo "Tests simulate:"
            echo "  - Network disconnection and reconnection"
            echo "  - Packet loss (30%)"
            echo "  - Message ordering"
            echo "  - Conflict resolution"
          '';
        };
      });
}