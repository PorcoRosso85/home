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
        
        crawlScript = pkgs.writeScriptBin "url-crawl" ''
          #!${pkgs.bash}/bin/bash
          exec ${pkgs.deno}/bin/deno run --allow-net ${./crawl.ts} "$@"
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
              ${pkgs.deno}/bin/deno fmt *.ts
            '');
          };
          
          lint = {
            type = "app";
            program = toString (pkgs.writeShellScript "lint" ''
              ${pkgs.deno}/bin/deno lint *.ts
            '');
          };
          
          typecheck = {
            type = "app";
            program = toString (pkgs.writeShellScript "typecheck" ''
              ${pkgs.deno}/bin/deno check *.ts
            '');
          };
          
          test = {
            type = "app";
            program = toString (pkgs.writeShellScript "test" ''
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