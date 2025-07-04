{
  description = "POC 13.2: Dynamic Service Orchestration";

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
            httpie
            # For service discovery simulation
            etcd
            consul
          ];

          shellHook = ''
            echo "🔄 POC 13.2: Dynamic Service Orchestration"
            echo "=========================================="
            echo ""
            echo "📋 Quick Start:"
            echo "  1. Run tests:     deno task test"
            echo "  2. Run demo:      deno task start"
            echo "  3. Watch mode:    deno task dev"
            echo ""
            echo "🎯 Key Features:"
            echo "  - Service Registry with auto-discovery"
            echo "  - Health checking with Circuit Breaker"
            echo "  - Dynamic routing with pluggable strategies"
            echo "  - Progressive deployment (Canary/Blue-Green)"
            echo ""
            echo "📊 Demo Scenarios:"
            echo "  - New container auto-discovery"
            echo "  - Failed container auto-exclusion"
            echo "  - Canary deployment at 20%"
            echo ""
            echo "🔧 Advanced Usage:"
            echo "  # With etcd backend (future):"
            echo "  etcd &"
            echo "  REGISTRY_BACKEND=etcd deno run --allow-net demo.ts"
            echo ""
          '';
        };

        packages = {
          # Docker image for the orchestrator
          orchestratorImage = pkgs.dockerTools.buildImage {
            name = "poc13-orchestrator";
            tag = "latest";
            
            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [ pkgs.deno ];
              pathsToLink = [ "/bin" ];
            };
            
            config = {
              Cmd = [ "${pkgs.deno}/bin/deno" "run" "--allow-net" "--allow-env" "/app/demo.ts" ];
              WorkingDir = "/app";
              ExposedPorts = {
                "8080/tcp" = {};  # Main service port
                "9090/tcp" = {};  # Admin/metrics port
              };
              Env = [
                "DISCOVERY_INTERVAL=5000"
                "HEALTH_CHECK_INTERVAL=10000"
              ];
            };
          };

          # Test application image
          testAppImage = pkgs.dockerTools.buildImage {
            name = "poc13-test-app";
            tag = "latest";
            
            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [ pkgs.deno ];
              pathsToLink = [ "/bin" ];
            };
            
            config = {
              Cmd = [ 
                "${pkgs.deno}/bin/deno" 
                "eval" 
                ''
                  const port = parseInt(Deno.env.get("PORT") || "4001");
                  const id = Deno.env.get("SERVICE_ID") || "app-1";
                  
                  Deno.serve({ port }, (req) => {
                    const url = new URL(req.url);
                    if (url.pathname === "/health") {
                      return new Response(JSON.stringify({ 
                        status: "healthy", 
                        service: id,
                        timestamp: Date.now()
                      }), {
                        headers: { "content-type": "application/json" }
                      });
                    }
                    return new Response(JSON.stringify({
                      message: "Hello from " + id,
                      timestamp: Date.now()
                    }), {
                      headers: { "content-type": "application/json" }
                    });
                  });
                ''
              ];
              ExposedPorts = {
                "4001/tcp" = {};
              };
              Env = [
                "PORT=4001"
                "SERVICE_ID=app-1"
              ];
            };
          };
        };

        apps = {
          # Demo runner
          demo = flake-utils.lib.mkApp {
            drv = pkgs.writeShellScriptBin "poc13-demo" ''
              #!/usr/bin/env bash
              echo "🚀 Starting POC 13.2 Demo..."
              
              # Start test apps
              echo "Starting test applications..."
              
              # App 1
              SERVICE_ID=app-1 PORT=4001 ${pkgs.deno}/bin/deno eval '
                const port = parseInt(Deno.env.get("PORT") || "4001");
                const id = Deno.env.get("SERVICE_ID") || "app-1";
                console.log(`Starting ${id} on port ${port}`);
                Deno.serve({ port }, (req) => {
                  const url = new URL(req.url);
                  if (url.pathname === "/health") {
                    return new Response(JSON.stringify({ 
                      status: "healthy", 
                      service: id
                    }), {
                      headers: { "content-type": "application/json" }
                    });
                  }
                  return new Response(JSON.stringify({
                    message: `Hello from ${id}`,
                    timestamp: Date.now()
                  }), {
                    headers: { "content-type": "application/json" }
                  });
                });
              ' &
              APP1_PID=$!
              
              # App 2
              SERVICE_ID=app-2 PORT=4002 ${pkgs.deno}/bin/deno eval '
                const port = parseInt(Deno.env.get("PORT") || "4002");
                const id = Deno.env.get("SERVICE_ID") || "app-2";
                console.log(`Starting ${id} on port ${port}`);
                Deno.serve({ port }, (req) => {
                  const url = new URL(req.url);
                  if (url.pathname === "/health") {
                    return new Response(JSON.stringify({ 
                      status: "healthy", 
                      service: id
                    }), {
                      headers: { "content-type": "application/json" }
                    });
                  }
                  return new Response(JSON.stringify({
                    message: `Hello from ${id}`,
                    timestamp: Date.now()
                  }), {
                    headers: { "content-type": "application/json" }
                  });
                });
              ' &
              APP2_PID=$!
              
              sleep 2
              
              # Run orchestrator demo
              echo "Starting orchestrator demo..."
              ${pkgs.deno}/bin/deno run --allow-net --allow-env demo.ts
              
              # Cleanup
              kill $APP1_PID $APP2_PID 2>/dev/null
            '';
          };
        };
      });
}