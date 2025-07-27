{
  description = "External test for kuzu_py import capability";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    kuzu_py.url = "path:../..";  # Import kuzu_py from parent directory
  };

  outputs = { self, nixpkgs, flake-utils, kuzu_py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Import kuzu_py from the input
        kuzuPyPkg = kuzu_py.packages.${system}.kuzuPy;
        
        # Python environment with kuzu_py and pytest
        pythonEnv = pkgs.python312.withPackages (ps: [
          kuzuPyPkg
          ps.pytest
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
          
          shellHook = ''
            echo "External kuzu_py import test environment"
            echo "Python: $(python --version)"
          '';
        };
        
        # Test runner app
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test" ''
            echo "Running external import tests..."
            ${pythonEnv}/bin/pytest -v test_import.py
          ''}/bin/test";
        };
      });
}