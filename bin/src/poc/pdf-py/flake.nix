{
  description = "PDF analysis POC using pypdf2";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pypdf2
          requests
          pycryptodome
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
          ];
        };

        packages.default = pkgs.writeScriptBin "pdf-poc" ''
          #!${pkgs.bash}/bin/bash
          ${pythonEnv}/bin/python pdf.py "$@"
        '';
      });
}