{
  description = "Single Nix Container POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # シンプルなWebアプリケーション
        app = pkgs.writeShellScriptBin "entrypoint.sh" ''
          #!/usr/bin/env bash
          echo "Hello from Nix container!"
          echo "Available tools:"
          which curl && echo "- curl: $(curl --version | head -n1)"
          which jq && echo "- jq: $(jq --version)"
          which bash && echo "- bash: $(bash --version | head -n1)"
          
          # 簡易Webサーバーとして動作
          if [ "$1" = "serve" ]; then
            echo "Starting web server on port 8080..."
            while true; do
              echo -e "HTTP/1.1 200 OK\n\nHello from Nix container!" | nc -l -p 8080
            done
          fi
        '';
      in
      {
        # コンテナイメージのビルド
        packages.container = pkgs.dockerTools.buildImage {
          name = "hello-nix-container";
          tag = "latest";
          
          # コンテナの内容
          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = with pkgs; [
              # 基本的なツール
              bashInteractive
              coreutils
              curl
              jq
              netcat
              
              # アプリケーション
              app
            ];
            pathsToLink = [ "/bin" "/etc" ];
          };
          
          # コンテナ設定
          config = {
            Entrypoint = [ "/bin/entrypoint.sh" ];
            Env = [
              "NIX_CONTAINER=true"
              "PATH=/bin"
              "LANG=C.UTF-8"
            ];
            ExposedPorts = {
              "8080/tcp" = {};
            };
            WorkingDir = "/";
            Labels = {
              "org.nixos.container" = "true";
              "org.nixos.description" = "Single container POC";
            };
          };
        };
        
        # デフォルトパッケージ
        packages.default = self.packages.${system}.container;
        
        # 開発用シェル
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            docker
            skopeo
            dive # イメージ分析ツール
          ];
          
          shellHook = ''
            echo "Single Container Development Shell"
            echo ""
            echo "Commands:"
            echo "  nix build .#container   - Build container image"
            echo "  docker load < result    - Load into Docker"
            echo "  docker run hello-nix-container:latest"
            echo "  docker run -p 8080:8080 hello-nix-container:latest serve"
          '';
        };
      });
}