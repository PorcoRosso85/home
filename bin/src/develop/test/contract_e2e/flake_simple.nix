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
        
        # contract_e2e パッケージ  
        contractE2e = pkgs.python312Packages.buildPythonPackage rec {
          pname = "contract_e2e";
          version = "0.1.0";
          
          src = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type: 
              (pkgs.lib.hasSuffix ".py" path) ||
              (pkgs.lib.hasSuffix ".toml" path) ||
              (pkgs.lib.hasSuffix "setup.py" path) ||
              (baseNameOf path == "src");
          };
          
          # kuzu_pyと同じビルド方式
          pyproject = true;
          build-system = with pkgs.python312Packages; [
            setuptools
            wheel
          ];
          
          propagatedBuildInputs = with pkgs.python312Packages; [
            jsonschema
            hypothesis
          ];
          
          doCheck = false;
        };
        
        # Python環境
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          contractE2e
          pytest
          pytest-cov
        ]);
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
          
          shellHook = ''
            echo "Contract E2E Testing Framework"
            echo "Python: $(python --version)"
          '';
        };
        
        # パッケージ出力
        packages = {
          default = contractE2e;
          pythonEnv = pythonEnv;
        };
        
        # テストランナー
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test" ''
              cd ${./.}
              export PYTHONPATH="src:$PYTHONPATH"
              ${pythonEnv}/bin/pytest -v test_contract_e2e.py
            ''}/bin/test";
          };
          
          # 使用例デモ
          demo = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "demo" ''
              cd ${./examples/calculator}
              ${pythonEnv}/bin/python test_e2e.py
            ''}/bin/demo";
          };
        };
        
        # ライブラリ関数（シンプル版）
        lib = {
          runContractTest = { executable, inputSchema, outputSchema }:
            pkgs.writeShellScriptBin "contract-test" ''
              ${pythonEnv}/bin/python -c "
import json
from contract_e2e import run_contract_tests

with open('${inputSchema}') as f:
    input_schema = json.load(f)
with open('${outputSchema}') as f:
    output_schema = json.load(f)

result = run_contract_tests(
    executable='${executable}',
    input_schema=input_schema,
    output_schema=output_schema,
    test_count=1
)
print(json.dumps(result, indent=2))
"
            '';
        };
      });
}