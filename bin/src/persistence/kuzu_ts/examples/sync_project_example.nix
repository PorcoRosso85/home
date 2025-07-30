{
  description = "Example: Using packaged kuzu_ts in sync projects";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Reference the packaged kuzu_ts module
    kuzu-ts.url = "path:../../persistence/kuzu_ts";
    
    # Other dependencies your sync project might need
    log-ts.url = "path:../../telemetry/log_ts";
    storage-s3.url = "path:../../storage/s3";  # Optional
  };

  outputs = { self, nixpkgs, flake-utils, kuzu-ts, log-ts, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Get the packaged kuzu_ts with pre-installed node_modules
        kuzuTsPackage = kuzu-ts.packages.${system}.default;
        
      in
      {
        # Development shell with kuzu_ts properly linked
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            nodejs_20
            
            # Include the packaged kuzu_ts
            kuzuTsPackage
            
            # System libraries for native modules
            stdenv.cc.cc.lib
            
            # Development tools
            jq
            curl
            websocat
          ];
          
          shellHook = ''
            echo "🔄 Sync Project with Packaged KuzuDB TypeScript"
            echo "============================================="
            
            # Set up environment variables
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="${kuzuTsPackage}/lib"
            export LOG_TS_PATH="${log-ts.lib.importPath}"
            
            # Create symlinks for Deno imports
            # This allows using @kuzu-ts/ import prefix
            mkdir -p .deno-imports
            ln -sfn ${kuzuTsPackage}/lib .deno-imports/kuzu-ts
            ln -sfn ${log-ts.lib.importPath} .deno-imports/log_ts
            
            # Update deno.json imports (if not already configured)
            if [ -f deno.json ]; then
              echo "📦 Using existing deno.json"
            else
              cat > deno.json <<EOF
            {
              "tasks": {
                "test": "deno test --allow-all --unstable-worker-options",
                "server": "deno run --allow-all server.ts",
                "dev": "deno run --allow-all --watch server.ts"
              },
              "imports": {
                "@std/assert": "jsr:@std/assert@^1.0.0",
                "@std/async": "jsr:@std/async@^1.0.0",
                "@kuzu-ts/": "${kuzuTsPackage}/lib/",
                "@kuzu-ts/worker": "${kuzuTsPackage}/lib/mod_worker.ts",
                "log_ts/": "${log-ts.lib.importPath}/"
              },
              "nodeModulesDir": false
            }
            EOF
              echo "✅ Created deno.json with proper imports"
            fi
            
            echo ""
            echo "📍 Important paths:"
            echo "  - KuzuTS module: ${kuzuTsPackage}/lib/mod.ts"
            echo "  - KuzuTS worker: ${kuzuTsPackage}/lib/mod_worker.ts"
            echo "  - Node modules: ${kuzuTsPackage}/lib/node_modules"
            echo ""
            echo "🚀 You can now import kuzu_ts using:"
            echo '  import { KuzuTsClientImpl } from "@kuzu-ts/core/client/kuzu_ts_client.ts";'
            echo '  import { createWorker } from "@kuzu-ts/worker";'
          '';
        };
        
        # Server app using packaged kuzu_ts
        apps.server = {
          type = "app";
          program = "${pkgs.writeShellScript "start-server" ''
            # Ensure native modules can be loaded
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            
            # Set module paths
            export KUZU_TS_PATH="${kuzuTsPackage}/lib"
            export LOG_TS_PATH="${log-ts.lib.importPath}"
            
            echo "🚀 Starting server with packaged kuzu_ts..."
            exec ${pkgs.deno}/bin/deno run \
              --allow-net \
              --allow-read \
              --allow-write \
              --allow-env \
              --allow-ffi \
              --unstable-ffi \
              ./server.ts
          ''}";
        };
        
        # Test runner with packaged modules
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScript "run-tests" ''
            set -e
            
            # Set up environment
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="${kuzuTsPackage}/lib"
            export LOG_TS_PATH="${log-ts.lib.importPath}"
            export DENO_DIR="$(pwd)/.deno"
            
            echo "🧪 Running tests with packaged kuzu_ts..."
            
            # Run tests using the packaged modules
            ${pkgs.deno}/bin/deno test \
              --allow-all \
              --unstable-worker-options \
              --unstable-ffi \
              ./tests/*.test.ts
          ''}";
        };
        
        # Package the sync application
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "sync-kuzu-ts";
          version = "0.1.0";
          
          src = ./.;
          
          buildInputs = with pkgs; [
            deno
            kuzuTsPackage
          ];
          
          buildPhase = ''
            runHook preBuild
            
            # Copy source files
            cp -r $src/* .
            
            # Link the packaged kuzu_ts modules
            mkdir -p node_modules
            ln -s ${kuzuTsPackage}/lib/node_modules/.deno node_modules/.deno
            
            # Update import paths in deno.json
            cat > deno.json <<EOF
            {
              "imports": {
                "@kuzu-ts/": "${kuzuTsPackage}/lib/",
                "@kuzu-ts/worker": "${kuzuTsPackage}/lib/mod_worker.ts",
                "log_ts/": "${log-ts.lib.importPath}/"
              }
            }
            EOF
            
            runHook postBuild
          '';
          
          installPhase = ''
            runHook preInstall
            
            mkdir -p $out/{bin,lib}
            
            # Copy application files
            cp -r core tests examples *.ts deno.json $out/lib/
            
            # Link kuzu_ts node_modules
            ln -s ${kuzuTsPackage}/lib/node_modules $out/lib/node_modules
            
            # Create wrapper script
            cat > $out/bin/sync-kuzu-ts <<EOF
            #!/bin/sh
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}:\$LD_LIBRARY_PATH"
            export KUZU_TS_PATH="${kuzuTsPackage}/lib"
            cd $out/lib
            exec ${pkgs.deno}/bin/deno run --allow-all "\$@"
            EOF
            chmod +x $out/bin/sync-kuzu-ts
            
            runHook postInstall
          '';
        };
      });
}