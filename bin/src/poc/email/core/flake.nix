{
  description = "Email Core - 招待マーケティングメールMVP";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    bun-flake.url = "path:/home/nixos/bin/src/flakes/bun";  # 親flake継承
  };
  
  outputs = { self, nixpkgs, flake-utils, bun-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # パッケージファースト開発：親flakeから継承
        packages.default = pkgs.buildEnv {
          name = "email-core";
          paths = [
            bun-flake.packages.${system}.default  # bun + typescript-language-server + biome
            # プロジェクト固有の追加依存があればここに
          ];
        };
        # devShellは意図的に定義しない（必要になるまで作らない）
      });
}