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

  outputs = { self, nixpkgs, nixpkgs-unstable, sops-nix }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    pkgs-unstable = nixpkgs-unstable.legacyPackages.${system};
  in {
    nixosConfigurations.nixos-vm = nixpkgs.lib.nixosSystem {
      inherit system;
      
      modules = [
        ./hosts/nixos-vm/default.nix
        ./modules/common.nix
        ./modules/secrets.nix
        sops-nix.nixosModules.sops
        # Temporarily commented out for structural separation
        # nixos-wsl.nixosModules.wsl
        # vscode-server.nixosModules.default
      ];
    };
    
    # Basic check to ensure the NixOS config evaluates/builds under `nix flake check`
    checks.${system}.nixos-vm = self.nixosConfigurations.nixos-vm.config.system.build.toplevel;
  };
}
