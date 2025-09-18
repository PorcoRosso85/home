{
  description = "KuzuDB Priority Recalculation UDF POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            stdenv.cc.cc.lib
            uv
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            echo "Priority Recalculation POC Development Environment"
            echo "Run 'uv venv && uv pip install -e .' to set up"
            echo "Run 'uv run pytest test_priority_recalculation.py -v' to run tests"
          '';
        };
      });
}