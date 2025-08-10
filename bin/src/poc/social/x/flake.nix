{
  description = "X.com Developer API ¥šŸ<POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          requests
          tweepy
          python-dotenv
          pytest
          black
          mypy
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            curl
            jq
          ];

          shellHook = ''
            echo "X.com Developer API POC°ƒ"
            echo "Python°ƒhAPI‹zÄüëL)(ïıgY"
          '';
        };

        packages.default = pkgs.writeScriptBin "x-api-poc" ''
          #!${pkgs.bash}/bin/bash
          echo "X.com Developer API POC’ŸLW~Y"
          # TODO: ŸÅŒká¤ó¹¯ê×È’|súY
        '';
      });
}