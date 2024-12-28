{
  description = "My NixOS configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixos-wsl.url = "github:nixos-wsl/nixos-wsl";
    # 必要に応じて他の flake を追加
  };

  outputs = { self, nixpkgs, nixos-wsl }:
    let
      system = "x86_64-linux"; # システムに合わせて変更
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          (final: prev: {
            unstable = import (builtins.fetchTarball {
              url = "https://github.com/NixOS/nixpkgs/archive/nixpkgs-unstable.tar.gz";
            }) { inherit (prev) system; };
          })
        ];
      };
    in {
      nixosConfigurations.default = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ./configuration.nix
          nixos-wsl.nixosModules.wsl # nixos-wsl のモジュールをインポート
        ];
      };
    };
}
