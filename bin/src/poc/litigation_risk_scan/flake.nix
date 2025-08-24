{
  description = "Litigation Risk Scanner - 4Ñ¿üóúÄüë";

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
            bun
          ];

          shellHook = ''
            echo "= Litigation Risk Scanner"
            echo "ŸL: bun run main.ts"
          '';
        };

        apps.default = {
          type = "app";
          program = "${pkgs.bun}/bin/bun run ${self}/main.ts";
        };
      });
}