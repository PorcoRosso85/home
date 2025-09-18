{
  description = "POC 13.1: Envoy N Servers Extension";

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
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            curl
            jq
            vegeta
            k6
          ];

          shellHook = ''
            echo "🔄 POC 13.1: Envoy N Servers Extension"
            echo "====================================="
            echo ""
            echo "📋 Quick Start:"
            echo "  1. Start N backend servers:  ./start-n-servers.sh 5"
            echo "  2. Start Envoy proxy:       deno task start"
            echo "  3. Run demo:                ./demo.sh"
            echo "  4. Run load test:           ./load-test.sh"
            echo ""
            echo "🔧 Environment Variables:"
            echo "  BACKEND_SERVERS  - Server list (default: localhost:4001,localhost:4002,localhost:4003)"
            echo "  LB_STRATEGY      - Strategy: round-robin|random|least-conn (default: round-robin)"
            echo "  PROXY_PORT       - Proxy port (default: 8080)"
            echo "  ADMIN_PORT       - Admin port (default: 9901)"
            echo ""
            echo "📊 Examples:"
            echo "  # 10 servers with random strategy"
            echo "  BACKEND_SERVERS=\$(seq 1 10 | xargs -I{} echo -n localhost:400{}\\,| sed 's/,$//')"
            echo "  LB_STRATEGY=random deno task start"
            echo ""
          '';
        };

        packages = {
          # Docker image for the proxy
          proxyImage = pkgs.dockerTools.buildImage {
            name = "poc13-envoy-proxy";
            tag = "latest";
            
            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [ pkgs.deno ];
              pathsToLink = [ "/bin" ];
            };
            
            config = {
              Cmd = [ "${pkgs.deno}/bin/deno" "run" "--allow-net" "--allow-env" "/app/envoy-n-servers.ts" ];
              WorkingDir = "/app";
              ExposedPorts = {
                "8080/tcp" = {};
                "9901/tcp" = {};
              };
              Env = [
                "BACKEND_SERVERS=backend1:4001,backend2:4002,backend3:4003"
                "LB_STRATEGY=round-robin"
                "PROXY_PORT=8080"
                "ADMIN_PORT=9901"
              ];
            };
          };
        };
      });
}