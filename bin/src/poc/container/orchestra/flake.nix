{
  description = "Nix Container Orchestration POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    arion.url = "github:hercules-ci/arion";
  };

  outputs = { self, nixpkgs, flake-utils, arion }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Webアプリケーション
        webApp = pkgs.writeShellScriptBin "web-server" ''
          #!/usr/bin/env bash
          echo "Web server starting on port 80..."
          while true; do
            echo -e "HTTP/1.1 200 OK\n\n<h1>Web Server</h1><p>Connected to API at $API_URL</p>" | nc -l -p 80
          done
        '';
        
        # APIアプリケーション
        apiApp = pkgs.writeShellScriptBin "api-server" ''
          #!/usr/bin/env bash
          echo "API server starting on port 3000..."
          while true; do
            echo -e "HTTP/1.1 200 OK\nContent-Type: application/json\n\n{\"status\":\"ok\",\"db\":\"$DATABASE_URL\"}" | nc -l -p 3000
          done
        '';
        
      in
      {
        # コンテナイメージのエクスポート
        packages = rec {
          containers = {
            web = pkgs.dockerTools.buildImage {
              name = "web-container";
              tag = "latest";
              copyToRoot = pkgs.buildEnv {
                name = "web-root";
                paths = [ pkgs.bashInteractive pkgs.coreutils pkgs.netcat webApp ];
              };
              config = {
                Entrypoint = [ "/bin/web-server" ];
                ExposedPorts = { "80/tcp" = {}; };
              };
            };
            
            api = pkgs.dockerTools.buildImage {
              name = "api-container";
              tag = "latest";
              copyToRoot = pkgs.buildEnv {
                name = "api-root";
                paths = [ pkgs.bashInteractive pkgs.coreutils pkgs.netcat apiApp ];
              };
              config = {
                Entrypoint = [ "/bin/api-server" ];
                ExposedPorts = { "3000/tcp" = {}; };
              };
            };
            
            db = pkgs.dockerTools.buildImage {
              name = "postgres";
              tag = "14";
              copyToRoot = pkgs.buildEnv {
                name = "db-root";
                paths = [ pkgs.postgresql_14 ];
              };
              config = {
                Entrypoint = [ "${pkgs.postgresql_14}/bin/postgres" ];
                ExposedPorts = { "5432/tcp" = {}; };
              };
            };
          };
          
          web-container = containers.web;
          api-container = containers.api;
          db-container = containers.db;
        };
        
        # Arion設定
        arionProject = {
          services = {
            web = {
              image.nix = self.packages.${system}.containers.web;
              ports = [ "8080:80" ];
              environment = {
                API_URL = "http://api:3000";
              };
              depends_on = [ "api" ];
              healthcheck = {
                test = [ "CMD" "nc" "-z" "localhost" "80" ];
                interval = "30s";
                timeout = "3s";
                retries = 3;
              };
            };
            
            api = {
              image.nix = self.packages.${system}.containers.api;
              ports = [ "3000:3000" ];
              environment = {
                DATABASE_URL = "postgres://postgres:secret@db:5432/myapp";
              };
              depends_on = [ "db" ];
              healthcheck = {
                test = [ "CMD" "nc" "-z" "localhost" "3000" ];
                interval = "30s";
                timeout = "3s";
                retries = 3;
              };
            };
            
            db = {
              image = "postgres:14";
              environment = {
                POSTGRES_PASSWORD = "secret";
                POSTGRES_DB = "myapp";
              };
              volumes = [ "db-data:/var/lib/postgresql/data" ];
              healthcheck = {
                test = [ "CMD-SHELL" "pg_isready -U postgres" ];
                interval = "10s";
                timeout = "5s";
                retries = 5;
              };
            };
          };
          
          networks = {
            default = {
              driver = "bridge";
            };
          };
          
          volumes = {
            db-data = {};
          };
        };
        
        # arion実行用アプリ
        apps.arion = {
          type = "app";
          program = "${pkgs.writeShellScript "arion-wrapper" ''
            #!${pkgs.bash}/bin/bash
            ${arion.packages.${system}.arion}/bin/arion "$@"
          ''}";
        };
        
        # NixOS Container設定（代替実装）
        nixosConfigurations.container-cluster = nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            ({ config, pkgs, ... }: {
              # 基本的な設定
              system.stateVersion = "23.11";
              
              # コンテナ定義
              containers = {
                web = {
                  autoStart = true;
                  privateNetwork = true;
                  hostAddress = "192.168.100.10";
                  localAddress = "192.168.100.11";
                  
                  config = { config, pkgs, ... }: {
                    services.nginx = {
                      enable = true;
                      virtualHosts.default = {
                        locations."/" = {
                          return = "200 'Web Container Running'";
                        };
                      };
                    };
                  };
                };
                
                api = {
                  autoStart = true;
                  privateNetwork = true;
                  hostAddress = "192.168.100.20";
                  localAddress = "192.168.100.21";
                  
                  config = { config, pkgs, ... }: {
                    systemd.services.api = {
                      wantedBy = [ "multi-user.target" ];
                      script = ''
                        ${apiApp}/bin/api-server
                      '';
                    };
                  };
                };
              };
            })
          ];
        };
        
        # 開発シェル
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            docker
            docker-compose
            arion.packages.${system}.arion
          ];
          
          shellHook = ''
            echo "Orchestra Development Shell"
            echo ""
            echo "Commands:"
            echo "  nix build .#web-container  - Build web container"
            echo "  nix build .#api-container  - Build API container" 
            echo "  nix run .#arion -- config  - Generate docker-compose.yml"
            echo "  nix run .#arion -- up      - Start services"
          '';
        };
      });
}