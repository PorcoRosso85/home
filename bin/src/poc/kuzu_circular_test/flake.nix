{
  description = "KuzuDB Circular Dependency Detection POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python環境 - KuzuDBのみ
        pythonEnv = pkgs.python312.withPackages (ps: [
          ps.kuzu
        ]);
        
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
          
          shellHook = ''
            echo "KuzuDB Circular Dependency Detection POC"
            echo "Run: python test_circular.py"
          '';
        };
        
        apps = {
          default = {
            type = "app";
            program = "${pkgs.writeShellScript "test-circular" ''
              cd ${self}
              exec ${pythonEnv}/bin/python test_circular.py
            ''}";
          };
        };
      });
}