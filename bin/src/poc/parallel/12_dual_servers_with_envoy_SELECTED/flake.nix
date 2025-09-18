{
  description = "POC 12: Dual Servers with Envoy Proxy";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Envoyの設定ファイル
        envoyConfig = pkgs.writeText "envoy.yaml" ''
          static_resources:
            listeners:
            - address:
                socket_address:
                  address: 0.0.0.0
                  port_value: 8080
              filter_chains:
              - filters:
                - name: envoy.filters.network.http_connection_manager
                  typed_config:
                    "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                    stat_prefix: ingress_http
                    codec_type: AUTO
                    route_config:
                      name: local_route
                      virtual_hosts:
                      - name: backend
                        domains: ["*"]
                        routes:
                        - match:
                            prefix: "/"
                          route:
                            cluster: backend_cluster
                            timeout: 30s
                    http_filters:
                    - name: envoy.filters.http.router
                      typed_config:
                        "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
            
            clusters:
            - name: backend_cluster
              type: STRICT_DNS
              lb_policy: ROUND_ROBIN
              health_checks:
              - timeout: 5s
                interval: 10s
                unhealthy_threshold: 2
                healthy_threshold: 2
                http_health_check:
                  path: /health
              load_assignment:
                cluster_name: backend_cluster
                endpoints:
                - lb_endpoints:
                  - endpoint:
                      address:
                        socket_address:
                          address: server1
                          port_value: 4001
                  - endpoint:
                      address:
                        socket_address:
                          address: server2
                          port_value: 4002
            
            admin:
              address:
                socket_address:
                  address: 0.0.0.0
                  port_value: 9901
        '';

        # Envoyコンテナイメージ（Nix dockerTools使用）
        envoyImage = pkgs.dockerTools.buildImage {
          name = "poc12-envoy";
          tag = "latest";
          
          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = [ 
              pkgs.envoy 
              pkgs.busybox
            ];
            pathsToLink = [ "/bin" ];
          };
          
          config = {
            Cmd = [ "${pkgs.envoy}/bin/envoy" "-c" "/etc/envoy/envoy.yaml" ];
            ExposedPorts = {
              "8080/tcp" = {};
              "9901/tcp" = {};
            };
            Volumes = {
              "/etc/envoy" = {};
            };
          };
        };

        # テスト用のシンプルなHTTPサーバー
        testServer = pkgs.writeScriptBin "test-server" ''
          #!${pkgs.deno}/bin/deno run --allow-net
          
          const port = parseInt(Deno.env.get("PORT") || "4001");
          const serverName = Deno.env.get("SERVER_NAME") || "server-1";
          
          Deno.serve({ port }, (request) => {
            const url = new URL(request.url);
            
            if (url.pathname === "/health") {
              return new Response(JSON.stringify({ 
                status: "healthy",
                server: serverName,
                timestamp: Date.now()
              }), {
                headers: { "content-type": "application/json" }
              });
            }
            
            return new Response(JSON.stringify({
              message: "Hello from " + serverName,
              server: serverName,
              path: url.pathname,
              timestamp: Date.now()
            }), {
              headers: { "content-type": "application/json" }
            });
          });
        '';

      in
      {
        packages = {
          envoyImage = envoyImage;
          testServer = testServer;
          
          # Envoy設定ファイルをパッケージとして提供
          envoyConfig = pkgs.runCommand "envoy-config" {} ''
            mkdir -p $out
            cp ${envoyConfig} $out/envoy.yaml
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            envoy
            docker
            curl
            jq
            httpie
          ];

          shellHook = ''
            echo "🚀 POC 12: Dual Servers with Envoy Proxy"
            echo "========================================"
            echo ""
            echo "📋 Quick Start:"
            echo "  1. Build Envoy image:     nix build .#envoyImage"
            echo "  2. Load to Docker:        docker load < result"
            echo "  3. Start test servers:    ./start-servers.sh"
            echo "  4. Start Envoy:          ./start-envoy.sh"
            echo "  5. Run tests:            deno task test"
            echo ""
            echo "🔧 Useful commands:"
            echo "  curl localhost:8080/health"
            echo "  curl localhost:9901/stats/prometheus"
            echo "  http localhost:8080"
            echo ""
            echo "📊 Envoy Admin:"
            echo "  http://localhost:9901"
            echo ""
          '';
        };

        # アプリケーションスクリプト
        apps.default = flake-utils.lib.mkApp {
          drv = pkgs.writeShellScriptBin "poc12-demo" ''
            #!/usr/bin/env bash
            set -e
            
            echo "Starting POC 12 Demo..."
            
            # テストサーバー1を起動
            SERVER_NAME=server-1 PORT=4001 ${testServer}/bin/test-server &
            SERVER1_PID=$!
            
            # テストサーバー2を起動
            SERVER_NAME=server-2 PORT=4002 ${testServer}/bin/test-server &
            SERVER2_PID=$!
            
            # 少し待つ
            sleep 2
            
            # Envoyを起動
            ${pkgs.envoy}/bin/envoy -c ${envoyConfig} &
            ENVOY_PID=$!
            
            echo "All services started!"
            echo "- Server 1: http://localhost:4001"
            echo "- Server 2: http://localhost:4002"
            echo "- Envoy: http://localhost:8080"
            echo "- Envoy Admin: http://localhost:9901"
            echo ""
            echo "Press Ctrl+C to stop..."
            
            # クリーンアップ
            trap "kill $SERVER1_PID $SERVER2_PID $ENVOY_PID" EXIT
            
            # 待機
            wait
          '';
        };
      });
}