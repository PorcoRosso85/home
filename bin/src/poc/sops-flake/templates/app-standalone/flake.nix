{
  description = "Standalone application with sops-nix integration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, sops-nix, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages = {
          # Standalone application
          default = pkgs.writeShellScriptBin "my-app" ''
            set -euo pipefail
            
            # Runtime secret decryption (if age key exists)
            if [[ -f "$HOME/.config/sops/age/keys.txt" ]]; then
              export SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"
              
              # Decrypt secrets if available
              if [[ -f "./secrets/app.yaml" ]]; then
                echo "Loading encrypted secrets..."
                export API_KEY=$(${pkgs.sops}/bin/sops -d ./secrets/app.yaml | ${pkgs.yq}/bin/yq -r '.api_key')
              fi
            else
              echo "Warning: No age key found, running without secrets"
              export API_KEY="demo-key"
            fi
            
            # Simple web server example
            echo "Starting standalone app on port 8080..."
            echo "API Key configured: $([ -n "$API_KEY" ] && echo "Yes" || echo "No")"
            
            ${pkgs.writeScript "server.py" ''
              #!${pkgs.python3}/bin/python3
              import http.server
              import socketserver
              import os
              
              class Handler(http.server.SimpleHTTPRequestHandler):
                  def do_GET(self):
                      self.send_response(200)
                      self.send_header('Content-type', 'text/plain')
                      self.end_headers()
                      api_key = os.environ.get('API_KEY', 'not-set')
                      self.wfile.write(b'Standalone App Running\n')
                      self.wfile.write(f'API Key: {"Configured" if api_key != "not-set" else "Not configured"}\n'.encode())
              
              with socketserver.TCPServer(("", 8080), Handler) as httpd:
                  print('Server listening on port 8080')
                  httpd.serve_forever()
            ''}
          '';
          
          # Docker image
          container = pkgs.dockerTools.buildImage {
            name = "my-app";
            tag = "latest";
            
            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [ 
                self.packages.${system}.default
                pkgs.sops
              ];
            };
            
            config = {
              Cmd = [ "${self.packages.${system}.default}/bin/my-app" ];
              ExposedPorts = {
                "8080/tcp" = {};
              };
            };
          };
        };
        
        # Direct execution
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/my-app";
        };
        
        # Development shell
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            sops
            age
            ssh-to-age
            gnupg
            yq
            python3
          ];
          
          shellHook = ''
            echo "sops-flake development environment"
            echo "Available commands:"
            echo "  ./scripts/init-template.sh - Initialize template"
            echo "  ./scripts/setup-age-key.sh - Setup age key"
            echo "  ./scripts/verify-encryption.sh - Verify encryption"
            echo "  sops edit secrets/app.yaml - Edit encrypted secrets"
            echo "  nix run - Run the application"
            echo "  nix build .#container - Build container image"
            
            # Age key detection
            if [[ -f ~/.config/sops/age/keys.txt ]]; then
              export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
              echo "✓ Age key configured: $SOPS_AGE_KEY_FILE"
            fi
            
            # SSH key detection (新規追加)
            if [[ -f ~/.ssh/id_ed25519 ]] || [[ -f ~/.ssh/id_rsa ]]; then
              echo "✓ SSH keys available for age conversion"
              echo "  Convert to age: ssh-to-age -i ~/.ssh/id_ed25519.pub"
            fi
          '';
        };
      });
}