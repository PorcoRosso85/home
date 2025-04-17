{
  description = "SL build using flake-parts";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";

    # sl-src is defined here
    sl-src = {
      url = "github:mtoyoda/sl";
      flake = false;
    };
  };

  outputs = inputs@{ self, nixpkgs, flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      flake = {};
      
      perSystem = { config, self', inputs', pkgs, system, ... }: {
        _module.args.pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        
        # Default package and shell set to sl
        packages.default = config.packages.sl;
        devShells.default = config.devShells.sl;
      };

      imports = [
        # Import sl module
        ./sl/parts.nix
      ];
    };
}