{
  description = "Directory Scanner with FTS/VSS - Dynamic directory indexing and search";

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
            python311
            python311Packages.pytest
            python311Packages.pytest-timeout
            uv
            stdenv.cc.cc.lib  # For compiled dependencies
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Set default test environment
            export DIRSCAN_ROOT_PATH=''${DIRSCAN_ROOT_PATH:-.}
            export DIRSCAN_DB_PATH=''${DIRSCAN_DB_PATH:-:memory:}
            export DIRSCAN_INMEMORY=''${DIRSCAN_INMEMORY:-true}
            
            echo "Directory Scanner Development Environment"
            echo ""
            echo "Setup:"
            echo "  uv sync              - Install dependencies"
            echo ""
            echo "Run application:"
            echo "  uv run dirscan       - Run CLI"
            echo "  uv run python cli.py - Alternative CLI run"
            echo ""
            echo "Run tests:"
            echo "  uv run pytest        - Run all tests"
            echo "  uv run pytest -k <pattern> - Run specific tests"
            echo ""
            echo "Environment variables set:"
            echo "  DIRSCAN_ROOT_PATH=$DIRSCAN_ROOT_PATH"
            echo "  DIRSCAN_DB_PATH=$DIRSCAN_DB_PATH"
            echo "  DIRSCAN_INMEMORY=$DIRSCAN_INMEMORY"
          '';
        };

        # Simple app that requires nix develop
        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScript "dirscan-notice" ''
            echo "Directory Scanner requires 'nix develop' environment."
            echo ""
            echo "Usage:"
            echo "  1. nix develop"
            echo "  2. uv sync"
            echo "  3. uv run dirscan <command>"
            echo ""
            echo "Or for direct execution:"
            echo "  nix develop -c uv run dirscan <command>"
            exit 1
          ''}";
        };
      });
}