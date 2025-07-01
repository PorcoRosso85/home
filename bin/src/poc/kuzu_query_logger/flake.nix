{
  description = "KuzuDB Query Logger POC - ACID-compliant query logging";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pytest
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];

          shellHook = ''
            echo "KuzuDB Query Logger POC"
            echo "Commands:"
            echo "  nix run .#test        - Run pytest tests"
            echo "  nix run .#test-red    - Run TDD RED phase tests"
            echo "  nix run .#test-green  - Run GREEN phase implementation tests"
          '';
        };
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-tests" ''
            cd ${./.}
            ${pythonEnv}/bin/pytest -v kuzu_query_logger.py "$@"
          ''}";
        };
        
        apps.test-red = {
          type = "app";
          program = "${pkgs.writeShellScript "run-red-phase" ''
            echo "=== KuzuDB Query Logger - TDD RED PHASE ==="
            echo ""
            cd ${./.}
            ${pythonEnv}/bin/python kuzu_query_logger.py
          ''}";
        };
        
        apps.test-green = {
          type = "app";
          program = "${pkgs.writeShellScript "run-green-phase" ''
            echo "=== KuzuDB Query Logger - TDD GREEN PHASE ==="
            echo ""
            cd ${./.}
            ${pythonEnv}/bin/pytest -v kuzu_query_logger.py "$@"
          ''}";
        };
        
        apps.default = self.apps.${system}.test-red;
      });
}