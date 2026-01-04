{
  description = "Nix configuration (os + hm unified)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    sops-nix.url = "github:Mic92/sops-nix";

    nixos-wsl = {
      url = "github:nix-community/NixOS-WSL";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    home-manager = {
      url = "github:nix-community/home-manager/release-25.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      nixpkgs-unstable,
      sops-nix,
      nixos-wsl,
      home-manager,
    }:
    let
      system = "x86_64-linux";
    in
    {
      nixosConfigurations = {
        nixos-vm = nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            ./os/hosts/nixos-vm/default.nix
            ./os/modules/common.nix
            ./os/modules/secrets.nix
            sops-nix.nixosModules.sops
            (
              { lib, ... }:
              {
                _module.args.self = lib.mkDefault self;
              }
            )
          ];
        };

        y-wsl = nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            ./os/hosts/y-wsl/default.nix
            ./os/modules/common.nix
            ./os/modules/secrets.nix
            sops-nix.nixosModules.sops
            nixos-wsl.nixosModules.wsl
            home-manager.nixosModules.home-manager
            {
              home-manager.users.nixos = import ./hm/home.nix;
            }
            (
              { lib, ... }:
              {
                _module.args.self = lib.mkDefault self;
              }
            )
          ];
        };
      };

      homeConfigurations = {
        "nixos@y-wsl" = home-manager.lib.homeManagerConfiguration {
          pkgs = nixpkgs.legacyPackages.${system};
          modules = [ ./hm/home.nix ];
        };
      };
    };
}
