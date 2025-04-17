{
  description = "My custom development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    my-custom-flake.url =
      "github:PorcoRosso85/home/main?dir=nix/dev/python";
  };

  outputs = { self, nixpkgs, flake-utils, my-custom-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        customDevShell = my-custom-flake.devShells.${system}.default;
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
              nodePackages.typescript-language-server
            ]
            ++ customDevShell.buildInputs ;

          shellHook = ''
            echo "Welcome to the development environment!"
          '';
        };
      });
}
