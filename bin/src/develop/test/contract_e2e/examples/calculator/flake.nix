{
  description = "Calculator with contract-based E2E tests";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    contract-e2e.url = "path:../..";  # contract_e2eフレームワークへの相対パス
  };

  outputs = { self, nixpkgs, flake-utils, contract-e2e }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
      in
      {
        packages = {
          default = pkgs.writeScriptBin "calculator" ''
            #!${pkgs.bash}/bin/bash
            ${python}/bin/python ${./calculator.py}
          '';
        };

        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/calculator";
          };

          # contract_e2eフレームワークを使ったE2Eテスト
          test-e2e = {
            type = "app";
            program = "${contract-e2e.lib.${system}.mkContractE2ETest {
              name = "calculator";
              executable = "${self.packages.${system}.default}/bin/calculator";
              inputSchema = ./input.schema.json;
              outputSchema = ./output.schema.json;
              testCount = 10;  # デモ用に少なめに設定
            }}/bin/contract-e2e-test-calculator";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ python ];
          shellHook = ''
            echo "Calculator with Contract E2E Testing"
            echo "Run 'nix run' to execute calculator"
            echo "Run 'nix run .#test-e2e' to run contract-based tests"
          '';
        };
      });
}