{
  description = "mizchi/readability CLI tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        nodejs = pkgs.nodejs_20;
        
        # Use nodePackages for npm
        nodePackages = pkgs.nodePackages;
        
        # Create wrapper with proper npm setup
        readabilityWrapper = pkgs.writeShellScriptBin "readability" ''
          # Set up environment
          export PATH="${nodejs}/bin:${nodePackages.npm}/bin:$PATH"
          export NODE_PATH="${nodejs}/lib/node_modules"
          
          # Use a temporary directory for npm cache
          export NPM_CONFIG_CACHE="''${XDG_CACHE_HOME:-$HOME/.cache}/npm"
          export NPM_CONFIG_PREFIX="''${XDG_DATA_HOME:-$HOME/.local/share}/npm"
          
          # Ensure directories exist
          mkdir -p "$NPM_CONFIG_CACHE" "$NPM_CONFIG_PREFIX/bin"
          
          # Add npm prefix bin to PATH
          export PATH="$NPM_CONFIG_PREFIX/bin:$PATH"
          
          # Check if readability is installed
          if ! command -v readability &> /dev/null; then
            echo "Installing @mizchi/readability..." >&2
            ${nodePackages.npm}/bin/npm install -g @mizchi/readability
          fi
          
          # Execute readability
          exec readability "$@"
        '';
      in
      {
        packages.default = readabilityWrapper;
        
        apps.default = {
          type = "app";
          program = "${readabilityWrapper}/bin/readability";
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            nodePackages.npm
            readabilityWrapper
          ];

          shellHook = ''
            echo "mizchi/readability CLI environment"
            echo ""
            echo "The readability command is now available."
            echo ""
            echo "Usage:"
            echo "  readability -o article.md https://example.com/article"
            echo "  readability -f ai-summary https://example.com"
            echo "  readability --help"
          '';
        };
      });
}