{
  description = "Litigation Risk Scanner - 訴訟パターン検出ツール";

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
            # Python環境
            (python311.withPackages (ps: with ps; [
              pip
              setuptools
              wheel
            ]))
            
            # TypeScript環境
            bun
            
            # Database
            sqlite
          ];

          shellHook = ''
            echo "🔍 Litigation Risk Scanner (MVP)"
            echo ""
            echo "Python環境:"
            echo "  pip install edgartools"
            echo "  python store/ddl.py"
            echo "  python store/dml.py"
            echo ""
            echo "TypeScript実行:"
            echo "  bun run main.ts"
            echo ""
            echo "DB: risk.db"
          '';
        };

        apps.default = {
          type = "app";
          program = "${pkgs.bun}/bin/bun run ${self}/main.ts";
        };
      });
}