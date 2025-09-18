{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.services.sops-web-api;
in
{
  options.services.sops-web-api = {
    enable = mkEnableOption "Sops-enabled Web API service";
    
    port = mkOption {
      type = types.port;
      default = 8080;
      description = "Port to listen on";
    };
    
    secretsFile = mkOption {
      type = types.path;
      default = ./secrets/app.yaml;
      description = "Path to encrypted secrets file";
    };
  };
  
  config = mkIf cfg.enable {
    # Configure sops-nix for this service
    sops.secrets."web-api/api_key" = {
      sopsFile = cfg.secretsFile;
      owner = "web-api";
      group = "web-api";
      mode = "0400";
    };
    
    # Create service user
    users.users.web-api = {
      isSystemUser = true;
      group = "web-api";
      description = "Web API service user";
    };
    
    users.groups.web-api = {};
    
    # Define systemd service
    systemd.services.sops-web-api = {
      description = "Sops-enabled Web API";
      after = [ "network.target" "sops-nix.service" ];
      wants = [ "sops-nix.service" ];
      wantedBy = [ "multi-user.target" ];
      
      serviceConfig = {
        Type = "simple";
        User = "web-api";
        Group = "web-api";
        Restart = "always";
        RestartSec = 5;
        
        # Service will read the decrypted secret from this path
        Environment = [
          "API_KEY_FILE=${config.sops.secrets."web-api/api_key".path}"
          "PORT=${toString cfg.port}"
        ];
      };
      
      script = ''
        echo "Starting Web API on port ${toString cfg.port}..."
        
        # Read API key from decrypted file
        if [[ -f "$API_KEY_FILE" ]]; then
          export API_KEY=$(cat "$API_KEY_FILE")
          echo "✅ API key loaded successfully"
        else
          echo "⚠️  No API key file found, running without authentication"
        fi
        
        # Simple Python web server as demo
        ${pkgs.python3}/bin/python3 -c "
import http.server
import socketserver
import os

class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        api_key = os.environ.get('API_KEY', 'not-set')
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(f'Web API running on port ${toString cfg.port}\\n'.encode())
        self.wfile.write(f'API Key configured: {\"Yes\" if api_key != \"not-set\" else \"No\"}\\n'.encode())

with socketserver.TCPServer(('', ${toString cfg.port}), AuthHandler) as httpd:
    print(f'Server listening on port ${toString cfg.port}')
    httpd.serve_forever()
        "
      '';
    };
  };
}