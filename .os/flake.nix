{
  description = "NixOS system configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    
    sops-nix.url = "github:Mic92/sops-nix";
    
    # Temporarily commented out for structural separation
    # nixos-wsl = {
    #   url = "github:nix-community/NixOS-WSL";
    #   inputs.nixpkgs.follows = "nixpkgs";
    # };
    # 
    # vscode-server = {
    #   url = "github:nix-community/nixos-vscode-server";
    #   inputs.nixpkgs.follows = "nixpkgs";
    # };
  };

  outputs = { self, nixpkgs, nixpkgs-unstable, sops-nix, }:
  let
    system = "x86_64-linux";
  in {
    nixosConfigurations = {
      nixos-vm = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ./hosts/nixos-vm/default.nix  # ← VMのハード/boot
          ./modules/common.nix          # ← ソフト共通
          ./modules/secrets.nix
          sops-nix.nixosModules.sops
        ];
      };

      y-wsl = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ./hosts/y-wsl/default.nix     # ← yのWSL用設定（今の/etc/nixos相当）
          ./modules/common.nix          # ← ソフト共通（nixos-vmと同じもの）
          ./modules/secrets.nix
          sops-nix.nixosModules.sops
          # 必要なら nixos-wsl.nixosModules.wsl
        ];
      };
    };
  };
}
