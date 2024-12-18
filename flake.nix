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
      # nix build .#homeConfigurations.roccho.activationPackage
      homeConfigurations.nixos = home-manager.lib.homeManagerConfiguration {
        inherit pkgs;
        modules = [
          ./nix/home.nix
          {
            home = {
              username = "nixos";
              homeDirectory = "/home/nixos";
              # username = "${pkgs.lib.getEnv 'USER'}"; # あなたのユーザー名
              # homeDirectory = "/home/${pkgs.lib.getEnv 'USER'}"; # あなたのホームディレクトリ
              stateVersion = "23.11";
            };
          }
        ];
      };
    };
    
    # 以下はこのflakeで`nix develop`を行う場合に使用する
    #
    #  // flake-utils.lib.eachDefaultSystem (system: {
    #   # nix develop
    #   devShells.default = import ./develop.nix { inherit pkgs; };
    #   packages = {
    #     default = pkgs.writeShellScriptBin "default" ''
    #       echo "This is the default package"
    #     '';
    #   };
    #   defaultPackage = self.packages.${system}.default;
    #   # nix run
    #   apps = {
    #     webServer = flake-utils.lib.mkApp {
    #       drv = pkgs.writeShellScriptBin "webServer" ''
    #         #!/usr/bin/env bash
    #         echo "Starting web server"
    #         python3 -m http.server 8080
    #       '';
    #     };
    #   };
    # });
}
