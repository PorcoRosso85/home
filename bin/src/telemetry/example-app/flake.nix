{
  description = "Example application using telemetry log modules";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Import log modules as flake inputs
    log-ts.url = "path:../log_ts";
    log-py.url = "path:../log_py";
  };

  outputs = { self, nixpkgs, flake-utils, log-ts, log-py }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ 
            log-ts.overlays.default
            log-py.overlays.default
          ];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
            (python3.withPackages (ps: [ ps.log_py ]))
          ];
          
          shellHook = ''
            echo "Example app with telemetry log modules"
            echo "TypeScript log module available at: ${log-ts.lib.importPath}"
            echo "Python log module available as: log_py"
            echo ""
            echo "Try: nix run .#test-ts or nix run .#test-py"
          '';
        };
        
        apps = {
          # TypeScript example
          test-ts = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-ts" ''
              echo "=== Testing TypeScript log module ==="
              cat > test.ts << 'EOF'
              import { log } from "${log-ts.lib.importPath}/mod.ts";
              
              // Test basic logging
              log("INFO", { uri: "/test", message: "Hello from example app" });
              log("ERROR", { uri: "/api/error", message: "Test error", code: 500 });
              log("METRIC", { uri: "/metrics", message: "Performance", latency: 42.5 });
              EOF
              
              ${pkgs.deno}/bin/deno run test.ts
              rm test.ts
            ''}/bin/test-ts";
          };
          
          # Python example
          test-py = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test-py" ''
              echo "=== Testing Python log module ==="
              ${pkgs.python3.withPackages (ps: [ ps.log_py ])}/bin/python << 'EOF'
from log_py import log

# Test basic logging
log("INFO", {"uri": "/test", "message": "Hello from Python example"})
log("ERROR", {"uri": "/api/error", "message": "Test error", "code": 500})
log("METRIC", {"uri": "/metrics", "message": "Performance", "latency": 42.5})
EOF
            ''}/bin/test-py";
          };
          
          default = self.apps.${system}.test-ts;
        };
      });
}