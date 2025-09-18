{
  description = "URL Crawler - Extract links from websites";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Create a derivation that includes all source files
        src = pkgs.stdenv.mkDerivation {
          name = "url-crawler-src";
          src = ./.;
          phases = [ "unpackPhase" "installPhase" ];
          installPhase = ''
            mkdir -p $out
            cp -r * $out/
          '';
        };
        
        crawlScript = pkgs.writeScriptBin "url-crawl" ''
          #!${pkgs.bash}/bin/bash
          exec ${pkgs.deno}/bin/deno run --allow-net ${src}/crawl.ts "$@"
        '';
      in
      {
        packages.default = crawlScript;
        
        apps = {
          default = {
            type = "app";
            program = "${crawlScript}/bin/url-crawl";
          };
          
          format = {
            type = "app";
            program = toString (pkgs.writeShellScript "format" ''
              ${pkgs.deno}/bin/deno fmt /home/nixos/bin/src/poc/crawl/url/*.ts
            '');
          };
          
          lint = {
            type = "app";
            program = toString (pkgs.writeShellScript "lint" ''
              ${pkgs.deno}/bin/deno lint /home/nixos/bin/src/poc/crawl/url/*.ts
            '');
          };
          
          typecheck = {
            type = "app";
            program = toString (pkgs.writeShellScript "typecheck" ''
              cd /home/nixos/bin/src/poc/crawl/url
              ${pkgs.deno}/bin/deno check *.ts
            '');
          };
          
          test = {
            type = "app";
            program = toString (pkgs.writeShellScript "test" ''
              cd /home/nixos/bin/src/poc/crawl/url
              ${pkgs.deno}/bin/deno test --allow-net *.test.ts
            '');
          };
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            deno
            crawlScript
          ];
          
          shellHook = ''
            echo "URL Crawler Development Environment"
            echo ""
            echo "Usage:"
            echo "  url-crawl https://example.com"
            echo "  url-crawl https://docs.example.com -m '/api/**' --json"
            echo ""
            echo "Development commands:"
            echo "  nix run .#format     # Format all TypeScript files"
            echo "  nix run .#lint       # Lint all TypeScript files"
            echo "  nix run .#typecheck  # Type check all TypeScript files"
            echo "  nix run .#test       # Run all tests"
          '';
        };
      });
}