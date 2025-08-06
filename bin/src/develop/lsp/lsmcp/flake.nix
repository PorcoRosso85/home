{
  description = "lsmcp - Language Service MCP server for AI agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        nodejs = pkgs.nodejs_20;
        
        # Language servers
        languageServers = with pkgs; [
          nodePackages.typescript-language-server
          nodePackages.typescript
          rust-analyzer
          gopls
          pyright
          nodePackages.vscode-langservers-extracted  # HTML, CSS, JSON
        ];
        
        lsmcp = pkgs.stdenv.mkDerivation {
          pname = "lsmcp";
          version = "0.1.0";
          
          src = ./.;
          
          nativeBuildInputs = with pkgs; [
            makeWrapper
          ];
          
          buildInputs = [
            nodejs
          ] ++ languageServers;
          
          dontBuild = true;
          
          installPhase = ''
            mkdir -p $out/bin
            
            # Create the wrapper script
            cat > $out/bin/lsmcp << 'EOF'
            #!${pkgs.bash}/bin/bash
            exec ${nodejs}/bin/npx -y @mizchi/lsmcp "$@"
            EOF
            
            chmod +x $out/bin/lsmcp
            
            # Wrap with proper PATH including all language servers
            wrapProgram $out/bin/lsmcp \
              --prefix PATH : ${pkgs.lib.makeBinPath ([ nodejs ] ++ languageServers)}
          '';
          
          meta = with pkgs.lib; {
            description = "Language Service MCP server";
            homepage = "https://github.com/mizchi/lsmcp";
            license = licenses.mit;
            platforms = platforms.all;
          };
        };
      in
      {
        packages = {
          default = lsmcp;
          lsmcp = lsmcp;
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs
            nodePackages.npm
            nodePackages.typescript
            nodePackages.typescript-language-server
          ];
          
          shellHook = ''
            echo "lsmcp development environment"
            echo "Node.js version: $(node --version)"
            echo ""
            echo "Available commands:"
            echo "  nix build       - Build the lsmcp executable"
            echo "  nix run         - Run lsmcp directly"
            echo ""
          '';
        };
        
        apps.default = {
          type = "app";
          program = "${lsmcp}/bin/lsmcp";
        };
      });
}