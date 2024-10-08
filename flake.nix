{
  description = "My Nix Home Configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # 適切なNixpkgsのバージョンを指定
    home-manager.url = "github:nix-community/home-manager"; # or your desired branch
  };

  outputs = { self, nixpkgs, home-manager }: {
    homeConfigurations.rocchoHome = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      # extraSpecialArgs = { inherit inputs; };
      modules = [
        ./home.nix
        {
          home = {
            username = "ubuntu"; # あなたのユーザー名
            homeDirectory = "/home/ubuntu"; # あなたのホームディレクトリ
            stateVersion = "23.11"; # 適切なバージョンに更新
          };
        }
      ];
    };
  };
}
