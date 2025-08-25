{
  description = "Vite RSC Cloudflare deployment POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          nodejs_22
          nodePackages.wrangler
        ];

        shellHook = ''
          echo "Cloudflare Workers development environment"
          echo "Available commands:"
          echo "  wrangler dev    - Start local development server"
          echo "  wrangler deploy - Deploy to Cloudflare"
          echo ""
        '';
      };
    };
}