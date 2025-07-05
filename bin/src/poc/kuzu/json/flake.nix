{
  description = "KuzuDB JSON POC";

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
          packages = with pkgs; [
            python311
            ruff
            uv
            # C++ runtime libraries for kuzu
            stdenv.cc.cc.lib
          ];
          
          # Automatically set library paths for KuzuDB
          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          
          shellHook = ''
            echo "KuzuDB JSON POC environment"
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
              echo "🧪 Running KuzuDB JSON tests..."
              exec ${pkgs.uv}/bin/uv run pytest -v "$@"
            ''}";
          };
          
          # Run demo
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo" ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
              echo "📋 Running KuzuDB JSON demo..."
              exec ${pkgs.uv}/bin/uv run python -m kuzu_json_poc "$@"
            ''}";
          };
        };
      });
}