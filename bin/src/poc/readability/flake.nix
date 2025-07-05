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
        
        # Build environment with pre-installed package
        readabilityEnv = pkgs.buildEnv {
          name = "readability-env";
          paths = [ nodejs ];
          pathsToLink = [ "/bin" ];
          extraOutputsToInstall = [ "bin" ];
          
          postBuild = ''
            # Create a temporary directory for npm operations
            export NPM_CONFIG_PREFIX=$out
            export NPM_CONFIG_CACHE=$TMPDIR/npm-cache
            export HOME=$TMPDIR
            
            mkdir -p $NPM_CONFIG_CACHE
            
            # Install the package globally in this environment
            $out/bin/npm install -g @mizchi/readability
          '';
        };
        
        # Simple wrapper that uses the pre-built environment
        readabilityWrapper = pkgs.writeShellScriptBin "readability" ''
          exec ${readabilityEnv}/bin/readability "$@"
        '';
      in
      {
        packages.default = readabilityWrapper;
        
        devShells.default = pkgs.mkShell {
          buildInputs = [ readabilityWrapper ];

          shellHook = ''
            echo "mizchi/readability CLI environment"
            echo ""
            echo "Usage:"
            echo "  readability -o article.md https://example.com/article"
            echo "  readability -f ai-summary https://example.com"
            echo "  readability --help"
          '';
        };
      });
}