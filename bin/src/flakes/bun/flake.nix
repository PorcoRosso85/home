{
  description = "Common Bun/TypeScript environment for bin/src projects";

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
        # Bun実行環境
        packages.bunEnv = pkgs.bun;
        
        # 開発ツール
        packages.typescript-language-server = pkgs.nodePackages.typescript-language-server;
        packages.biome = pkgs.biome;
        
        # 統合開発環境（最小構成）
        packages.default = pkgs.buildEnv {
          name = "bun-dev-env";
          paths = with pkgs; [
            bun
            nodePackages.typescript-language-server
            biome
          ];
        };
        
        # 開発シェル
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bun
            nodePackages.typescript-language-server
            biome
          ];
          
          shellHook = ''
            echo "Bun development environment loaded"
            echo "Available tools: bun, typescript-language-server, biome"
          '';
        };
      });
}