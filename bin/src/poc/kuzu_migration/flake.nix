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
            echo "=== ステージング環境テスト ==="
            ${pythonEnv}/bin/python schema_event_sourcing_stg.py
            echo -e "\n=== 本番環境テスト ==="
            ${pythonEnv}/bin/python schema_event_sourcing_prod.py
          ''}";
        };
        
        apps.test-stg = {
          type = "app";
          program = "${pkgs.writeShellScript "run-staging-tests" ''
            cd ${./.}
            ${pythonEnv}/bin/pytest -v schema_event_sourcing_stg.py "$@"
          ''}";
        };
        
        apps.test-prod = {
          type = "app";
          program = "${pkgs.writeShellScript "run-production-tests" ''
            cd ${./.}
            ${pythonEnv}/bin/pytest -v schema_event_sourcing_prod.py "$@"
          ''}";
        };
      });
}