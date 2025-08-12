{
  description = "lsmcp - Language Service MCP server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        lsmcpEnv = pkgs.buildEnv {
          name = "lsmcp-env";
          paths = with pkgs; [
            nodejs_20
            nodePackages.typescript-language-server
            nodePackages.typescript
            rust-analyzer
            gopls
            pyright
            nodePackages.vscode-langservers-extracted
          ];
        };
      in
      {
        packages.default = lsmcpEnv;
        
        devShells.default = pkgs.mkShell {
          buildInputs = [ lsmcpEnv ];
          shellHook = ''
            echo "lsmcp environment loaded"
          '';
        };
      });
}