{
  description = "Common Python environment for bin/src projects";

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
        # 共通のPython環境を提供
        packages.pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pytest
          pytest-json-report
        ]);
        
        # 開発ツール
        packages.pyright = pkgs.pyright;
        packages.ruff = pkgs.ruff;
      });
}
