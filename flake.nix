{
  description = "My custom development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    my-custom-flake.url =
      "github:PorcoRosso85/home/main?dir=nix/dev/python";
  };

  outputs = { self, nixpkgs, flake-utils, my-custom-flake }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        customDevShell = my-custom-flake.devShells.${system}.default;
        # kuzu-cli = import ./kuzu.nix { inherit pkgs; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = customDevShell.buildInputs ++ [
            pkgs.pyright
            pkgs.google-cloud-sdk
            pkgs.ruff
          ];

          shellHook = ''
            # ここにシェルの初期化スクリプトを追加
            echo "Welcome to the development environment!"

            echo 'alias for aider'
            alias aider="uvx --from aider-chat aider --dark-mode --no-auto-commits --auto-test"

            echo "source secret"
            . $HOME/secret.sh
            
            echo "join python venv"
            export PYTHONDONTWRITEBYTECODE=1
            . .venv/bin/activate

            echo "read project source"
            . ./doc/shell/source.sh
            . env.sh

            echo "update LD_LIBRARY_PATH"
            # export LD_LIBRARY_PATH=$(nix path-info nixpkgs#stdenv)/lib:$LD_LIBRARY_PATH
            # export LD_LIBRARY_PATH=$(nix path-info nixpkgs#stdenv.cc.lib)/lib:$LD_LIBRARY_PATH
            echo "もしlibstdc++.so.6 が見つからないエラーが発生した場合, findしてください"
            echo "❯ find /nix/store -name 'libstdc++.so.6'"
            export LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH

          '';
        };
      });
}
