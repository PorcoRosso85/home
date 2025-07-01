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
            ${pythonEnv}/bin/pytest -v "$@"
          ''}";
        };
        
        apps.test-red = {
          type = "app";
          program = "${pkgs.writeShellScript "run-red-phase" ''
            echo "=== 基本テスト ==="
            ${pythonEnv}/bin/python schema_event_sourcing.py
            echo -e "\n=== 本番レベルテスト ==="
            ${pythonEnv}/bin/python schema_event_sourcing_production.py
          ''}";
        };
        
        apps.test-prod = {
          type = "app";
          program = "${pkgs.writeShellScript "run-production-tests" ''
            cd ${./.}
            ${pythonEnv}/bin/pytest -v schema_event_sourcing_production.py "$@"
          ''}";
        };
      });
}