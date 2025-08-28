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
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Inherit development shell from base
        devShells.default = waku-base.devShells.${system}.default;

        # Inherit build and deploy scripts
        packages = {
          inherit (waku-base.packages.${system}) build deploy;
        };

        # App-specific configuration - only build and deploy for nix run
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
        
        # Development scripts (use with nix shell)
        # Example: nix shell . -c "npm test"
        # Example: nix shell . -c "npm run typecheck"
        # Note: Development commands should be run via nix shell for faster startup
      });
}