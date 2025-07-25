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
        packages.default = pkgs.writeShellScriptBin "s3-client" ''
          exec ${deno}/bin/deno run \
            --allow-read \
            --allow-write \
            --allow-env \
            --allow-net \
            ${./main.ts} "$@"
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
              cd ${./.}
              exec ${deno}/bin/deno test --allow-all
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