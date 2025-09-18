{
  description = "Web API service with sops-nix integration";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  
  outputs = { self, nixpkgs, sops-nix }: {
    nixosModules.default = ./module.nix;
    
    packages.x86_64-linux = let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in {
      default = pkgs.writeShellScriptBin "web-api" ''
        echo "Starting Web API on port 8080..."
        ${pkgs.python3}/bin/python3 -m http.server 8080
      '';
    };
  };
}