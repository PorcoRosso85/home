{
  description = "KuzuDB migration POC with pytest";

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
            echo "KuzuDB Migration POC"
            echo "Run tests: pytest -v"
          '';
        };
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-tests" ''
            cd ${./.}
            ${pythonEnv}/bin/pytest -v schema_event_sourcing.py "$@"
          ''}";
        };
        
        apps.test-red = {
          type = "app";
          program = "${pkgs.writeShellScript "run-red-phase" ''
            ${pythonEnv}/bin/python schema_event_sourcing.py
          ''}";
        };
      });
}