{
  description = "POC 13.3: Raft + Dynamic Service Orchestration Integration";

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
            echo "POC 13.3: Raft + Dynamic Service Orchestration Integration"
            echo "========================================================="
            echo ""
            echo "Available commands:"
            echo "  deno test integration.test.ts - Run integration tests"
            echo "  deno test ../raft/raft.test.ts - Run Raft unit tests"
            echo ""
          '';
        };
      }
    );
}