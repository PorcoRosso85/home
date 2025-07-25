{
  description = "S3 client abstraction library (TypeScript/Deno)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Deno environment
        deno = pkgs.deno;
      in
      {
        packages.default = let
          # Create a derivation that includes all source files
          s3Source = pkgs.stdenv.mkDerivation {
            name = "s3-client-source";
            src = ./.;
            phases = [ "unpackPhase" "installPhase" ];
            installPhase = ''
              mkdir -p $out
              cp -r * $out/
            '';
          };
        in pkgs.writeShellScriptBin "s3-client" ''
          # Create a temporary working directory
          WORK_DIR="$(mktemp -d)"
          export DENO_DIR="$WORK_DIR/.deno"
          
          # Copy source files to working directory
          cp -r ${s3Source}/* "$WORK_DIR/"
          cd "$WORK_DIR"
          
          # Clean up on exit
          trap "rm -rf $WORK_DIR" EXIT
          
          exec ${deno}/bin/deno run \
            --allow-read \
            --allow-write \
            --allow-env \
            --allow-net \
            --no-lock \
            ./main.ts "$@"
        '';

        devShells.default = pkgs.mkShell {
          buildInputs = [ deno ];
          
          shellHook = ''
            echo "S3 Client Development Environment (Deno)"
            echo "Available commands:"
            echo "  deno test --allow-all    - Run tests"
            echo "  deno run --allow-all main.ts - Run CLI"
            echo "  deno fmt                 - Format code"
            echo "  deno lint                - Lint code"
          '';
        };

        apps = rec {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/s3-client";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "run-tests" ''
              # Create temporary directory for test execution
              export TMPDIR=$(mktemp -d)
              export DENO_DIR=$TMPDIR/.deno
              
              # Copy source files to temp directory
              cp -r ${./.}/* $TMPDIR/ 2>/dev/null || true
              cd $TMPDIR
              
              # Run tests
              ${deno}/bin/deno test --allow-all --no-lock --no-check
              
              # Cleanup
              rm -rf $TMPDIR
            ''}";
          };
          
          fmt = {
            type = "app";
            program = "${pkgs.writeShellScript "format" ''
              cd ${./.}
              exec ${deno}/bin/deno fmt
            ''}";
          };
          
          lint = {
            type = "app";
            program = "${pkgs.writeShellScript "lint" ''
              cd ${./.}
              exec ${deno}/bin/deno lint
            ''}";
          };
        };
      });
}