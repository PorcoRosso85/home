{
  description = "My Nix Home Configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # 適切なNixpkgsのバージョンを指定
    home-manager.url = "github:nix-community/home-manager"; # or your desired branch
  };

  outputs = { self, nixpkgs, home-manager }: let
    # username = builtins.getEnv "USER";
    username = "roccho";
  in
  {
    homeConfigurations.rocchoHome = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      # extraSpecialArgs = { inherit inputs; };
      modules = [
        ./home.nix
        {
          home = {
            username = username; # あなたのユーザー名
            homeDirectory = "/home/${username}"; # あなたのホームディレクトリ
            stateVersion = "23.11"; # 適切なバージョンに更新
          };
        }
      ];
    };
  };
}
