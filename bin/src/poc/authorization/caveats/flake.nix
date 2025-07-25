{
  description = "SpiceDB Authorization POC with Caveats";

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
        packages = {
          spicedb = pkgs.spicedb;
          default = pkgs.spicedb;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            spicedb
            curl
            jq
          ];

          shellHook = ''
            echo "SpiceDB Authorization POC Development Environment"
            echo "Available commands:"
            echo "  spicedb serve - Start SpiceDB server"
            echo "  curl - HTTP client for API testing"
            echo "  jq - JSON processor"
          '';
        };
      });
}