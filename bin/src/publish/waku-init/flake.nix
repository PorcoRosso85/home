{
  description = "Waku application using waku_node base";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    waku-base = {
      url = "path:../../poc/vite_rsc/waku_node";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils, waku-base }:
    flake-utils.lib.eachDefaultSystem (system:
      {
        # Inherit development shell from base
        devShells.default = waku-base.devShells.${system}.default;

        # Inherit build and deploy scripts
        packages = {
          inherit (waku-base.packages.${system}) build deploy;
        };

        # App-specific configuration
        apps = {
          build = {
            type = "app";
            program = "${waku-base.packages.${system}.build}/bin/waku-build";
          };
          deploy = {
            type = "app";
            program = "${waku-base.packages.${system}.deploy}/bin/waku-deploy";
          };
        };
      });
}