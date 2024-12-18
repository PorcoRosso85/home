{
  description = "My Nix Home Configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # 適切なNixpkgsのバージョンを指定
    flake-utils.url = "github:numtide/flake-utils";
    home-manager = {
      url = "github:nix-community/home-manager"; # or your desired branch
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, home-manager }:
    let
      system = "x86_64-linux";  # homeのためにシステムを明示的に指定
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      homeConfigurations.roccho = home-manager.lib.homeManagerConfiguration {
        inherit pkgs;
        modules = [
          ./nix/home.nix
          {
            home = {
              username = "nixos";
              homeDirectory = "/home/nixos";
              # username = "${pkgs.lib.getEnv 'USER'}"; # あなたのユーザー名
              # homeDirectory = "/home/${pkgs.lib.getEnv 'USER'}"; # あなたのホームディレクトリ
              stateVersion = "24.05";
            };
          }
        ];
      };
    };
}
