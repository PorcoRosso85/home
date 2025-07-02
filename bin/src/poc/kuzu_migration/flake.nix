{
  description = "A development environment for the kuzu_migration project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      # Supported systems
      systems = [ "x86_64-linux" "aarch64-linux" ];

      # Helper function to generate a devShell for each system
      forAllSystems = nixpkgs.lib.genAttrs systems;

    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            # The Nix packages available in the development environment
            packages = [
              pkgs.python3
              pkgs.ruff
              pkgs.uv # For managing python dependencies
            ];
          };
        });
    };
}
