{
  description = "KuzuDB Network Sync POC - Real network condition testing";

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
            echo "KuzuDB Network Sync POC"
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
            ${pythonEnv}/bin/pytest -v network_sync.py "$@"
          ''}";
        };
        
        apps.test-red = {
          type = "app";
          program = "${pkgs.writeShellScript "run-red-phase" ''
            echo "=== KuzuDB Network Sync - TDD RED PHASE ==="
            echo ""
            cd ${./.}
            ${pythonEnv}/bin/python network_sync.py
          ''}";
        };
        
        apps.test-green = {
          type = "app";
          program = "${pkgs.writeShellScript "run-green-phase" ''
            echo "=== KuzuDB Network Sync - TDD GREEN PHASE ==="
            echo ""
            cd ${./.}
            ${pythonEnv}/bin/pytest -v network_sync.py "$@"
          ''}";
        };
        
        apps.default = self.apps.${system}.test-red;
      });
}