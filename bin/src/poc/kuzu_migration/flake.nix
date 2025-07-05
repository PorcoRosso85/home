{
  description = "A development environment for the kuzu_migration project";

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
          # The Nix packages available in the development environment
          packages = with pkgs; [
            python311
            ruff
            uv # For managing python dependencies
            # C++ runtime libraries for kuzu
            stdenv.cc.cc.lib
          ];
          
          # Automatically set library paths for KuzuDB
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          
          shellHook = ''
            echo "KuzuDB Migration Framework Development Environment"
            echo "Python: $(python --version)"
            echo ""
            echo "Commands:"
            echo "  uv sync                    - Install dependencies"
            echo "  uv run pytest -v           - Run all tests"
            echo "  nix run .#test             - Run tests via nix"
          '';
        };
        
        # Applications
        apps = {
          # Test runner
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "🧪 Running KuzuDB Migration tests..."
              exec ${pkgs.uv}/bin/uv run pytest -v "$@"
            ''}";
          };
          
          # Run example usage
          example = {
            type = "app";
            program = "${pkgs.writeShellScript "example" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "📋 Running example usage..."
              exec ${pkgs.uv}/bin/uv run python example_usage.py "$@"
            ''}";
          };
        };
      });
}