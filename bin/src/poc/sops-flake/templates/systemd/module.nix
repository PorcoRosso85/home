{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.services.my-service;
in
{
  options.services.my-service = {
    enable = mkEnableOption "My systemd service with sops";
    
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
    
    user = mkOption {
      type = types.str;
      default = "my-service";
      description = "User to run the service as";
    };
    
    # New options for unified configuration
    encryptionMethod = mkOption {
      type = types.enum ["age" "ssh"];
      default = "age";
      description = "Encryption method for sops";
    };
    
    environment = mkOption {
      type = types.enum ["development" "staging" "production"];
      default = "development";
      description = "Deployment environment";
    };
    
    sopsKeyPath = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Path to sops key file (age key or SSH key)";
    };
  };
  
  config = mkIf cfg.enable {
    # Import sops-nix module if not already imported
    imports = [ ];
    
    # Configure sops based on encryption method
    sops = if cfg.encryptionMethod == "age" then {
      age.sshKeyPaths = [ ];
      age.keyFile = cfg.sopsKeyPath;
    } else {
      age.sshKeyPaths = 
        if cfg.sopsKeyPath != null
        then [ cfg.sopsKeyPath ]
        else [ "/etc/ssh/ssh_host_ed25519_key" ];
    };
    
    # Configure sops secrets
    sops.secrets."api_key" = {
      sopsFile = cfg.secretsFile;
      owner = cfg.user;
      group = cfg.user;
      mode = "0400";
    };
    
    sops.secrets."db_password" = {
      sopsFile = cfg.secretsFile;
      owner = cfg.user;
      group = cfg.user;
      mode = "0400";
    };
    
    sops.secrets."jwt_secret" = {
      sopsFile = cfg.secretsFile;
      owner = cfg.user;
      group = cfg.user;
      mode = "0400";
    };
    
    # Create service user
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.user;
      description = "My service user";
    };
    
    users.groups.${cfg.user} = {};
    
    # Define systemd service
    systemd.services.my-service = {
      description = "My systemd service with secrets";
      after = [ "network.target" "sops-nix.service" ];
      wants = [ "sops-nix.service" ];
      wantedBy = [ "multi-user.target" ];
      
      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Group = cfg.user;
        Restart = "always";
        RestartSec = 5;
        
        # Service reads decrypted secrets from these paths
        Environment = [
          "PORT=${toString cfg.port}"
        ];
        
        # Load secrets as environment files
        EnvironmentFile = [
          config.sops.secrets."api_key".path
          config.sops.secrets."db_password".path
        ];
      };
      
      script = ''
        echo "Starting service on port ${toString cfg.port}..."
        echo "Environment: ${cfg.environment}"
        echo "Encryption method: ${cfg.encryptionMethod}"
        
        # Read secrets
        API_KEY=$(cat ${config.sops.secrets."api_key".path})
        DB_PASSWORD=$(cat ${config.sops.secrets."db_password".path})
        JWT_SECRET=$(cat ${config.sops.secrets."jwt_secret".path})
        
        echo "✅ Service started with configured secrets"
        
        # Simple HTTP server as example
        ${pkgs.python3}/bin/python3 -c "
import http.server
import socketserver
import os

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Systemd Service Running\\n')
        self.wfile.write(b'Port: ${toString cfg.port}\\n')
        self.wfile.write(b'Secrets: Configured\\n')

with socketserver.TCPServer(('', ${toString cfg.port}), Handler) as httpd:
    print('Service listening on port ${toString cfg.port}')
    httpd.serve_forever()
        "
      '';
    };
  };
}