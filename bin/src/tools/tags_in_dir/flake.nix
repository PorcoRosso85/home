{
  description = "tags_in_dir - ctags-based code analysis with KuzuDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          # Core dependencies
          kuzu
          
          # Development tools
          pytest
          pyright
          black
          ruff
          mypy
          
          # Type stubs
          types-setuptools
        ]);

        tags-in-dir = pkgs.python311Packages.buildPythonPackage rec {
          pname = "tags-in-dir";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pkgs.python311Packages; [
            kuzu
          ];
          
          nativeBuildInputs = with pkgs; [
            universal-ctags
          ];
          
          # No setup.py needed for module-only usage
          format = "other";
          
          installPhase = ''
            mkdir -p $out/lib/python3.11/site-packages/tags_in_dir
            cp -r . $out/lib/python3.11/site-packages/tags_in_dir/
          '';
        };

      in
      {
        # Default package is the Python environment with the library
        packages.default = pythonEnv;
        
        # The library package itself
        packages.tags-in-dir = tags-in-dir;
        
        # CLI application
        apps.default = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "tags-in-dir" ''
            export PYTHONPATH="${./.}:$PYTHONPATH"
            exec ${pythonEnv}/bin/python -m tags_in_dir.main "$@"
          ''}/bin/tags-in-dir";
        };
        
        # Alternative app names
        apps.generate = self.apps.${system}.default;
        apps.tags-in-dir = self.apps.${system}.default;
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            universal-ctags
            
            # Additional development tools
            entr
            jq
            ripgrep
          ];
          
          shellHook = ''
            echo "tags_in_dir development environment"
            echo "Python: ${pythonEnv}/bin/python"
            echo "ctags: ${pkgs.universal-ctags}/bin/ctags"
            echo ""
            echo "Commands:"
            echo "  nix run . -- <uri>              # Process URI"
            echo "  nix run . -- --help             # Show help"
            echo "  python -m pytest                # Run tests"
            echo "  pyright                         # Type check"
            echo "  black .                         # Format code"
            echo "  ruff check .                    # Lint code"
            echo ""
            
            # Set PYTHONPATH for development
            export PYTHONPATH="${./.}:$PYTHONPATH"
          '';
        };
      });
}