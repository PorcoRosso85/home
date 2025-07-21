{
  description = "Contract-based E2E testing framework using JSON Schema";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python311;
        
        # contract_e2e パッケージ
        contractE2e = pkgs.python311Packages.buildPythonPackage rec {
          pname = "contract_e2e";
          version = "0.1.0";
          
          src = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type: 
              (pkgs.lib.hasSuffix ".py" path) ||
              (pkgs.lib.hasSuffix ".toml" path) ||
              (baseNameOf path == "src");
          };
          
          format = "setuptools";
          
          propagatedBuildInputs = with pkgs.python311Packages; [
            jsonschema
            hypothesis
          ];
          
          # pythonImportsCheck = [ "contract_e2e" ];
          doCheck = false;
        };
        
        # Python環境
        pythonEnv = python.withPackages (ps: with ps; [
          contractE2e
          pytest
          pytest-cov
        ]);
      in
      {
        # パッケージ出力
        packages = {
          default = contractE2e;
          pythonEnv = pythonEnv;
        };
        
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            ruff
            uv
          ];
          
          shellHook = ''
            echo "Contract E2E Testing Framework"
            echo "Python: $(python --version)"
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
          '';
        };
        
        # アプリケーション
        apps = {
          test = {
            type = "app";
            program = toString (pkgs.writeScript "test" ''
              #!${pkgs.bash}/bin/bash
              cd /home/nixos/bin/src/develop/test/contract_e2e
              export PYTHONPATH="src:$PYTHONPATH"
              exec ${pythonEnv}/bin/pytest -v test_contract_e2e.py
            '');
          };
        };
        
        # ライブラリ関数
        lib = {
          mkContractE2ETest = { name, executable, inputSchema, outputSchema, testCount ? 100, timeout ? 3000, verbose ? false }:
            pkgs.writeShellApplication {
              name = "contract-e2e-test-${name}";
              runtimeInputs = [ pythonEnv ];
              text = ''
                exec ${pythonEnv}/bin/python -m contract_e2e.runner \
                  --name "${name}" \
                  --executable "${executable}" \
                  --input-schema "${inputSchema}" \
                  --output-schema "${outputSchema}" \
                  --test-count ${toString testCount} \
                  --timeout ${toString timeout} \
                  ${if verbose then "--verbose" else ""}
              '';
            };
        };
      });
}