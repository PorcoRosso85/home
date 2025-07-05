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
        
        apps.default = {
          type = "app";
          program = "${crawlScript}/bin/url-crawl";
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
            echo "  deno run --allow-net crawl.ts --help"
            echo ""
            echo "Development:"
            echo "  deno fmt crawl.ts     # Format code"
            echo "  deno lint crawl.ts    # Lint code"
            echo "  deno check crawl.ts   # Type check"
          '';
        };
      });
}