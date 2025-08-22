{
  description = "Sliplane deployment tools";

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
        # hello-nixµÖ×í¸§¯È’Âg
        packages.dockerImage = (import ./hello-nix/flake.nix).outputs 
          { inherit self nixpkgs flake-utils; }
          .packages.${system}.dockerImage;

        # ‹z·§ë
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            docker
            docker-compose
            git
            curl
          ];
        };
      });
}