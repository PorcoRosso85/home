{
  description = "Example flake using flake-parts with readme validation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-readme.url = "path:../..";
  };

  outputs = inputs@{ flake-parts, flake-readme, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        flake-readme.flakeModules.readme
      ];
      
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      
      perSystem = { pkgs, system, ... }: {
        # Enable readme.nix validation
        readme = {
          enable = true;
          root = ./.;
          ignoreExtra = [ "build" ];
          policy = {
            strict = false;
            failOnUnknownOutputKeys = false;
          };
        };
        
        # Your other perSystem config...
        packages.hello = pkgs.hello;
      };
    };
}