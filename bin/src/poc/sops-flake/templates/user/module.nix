{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.programs.user-script;
  
  userScript = pkgs.writeShellScriptBin "user-script" ''
    #!/usr/bin/env bash
    set -euo pipefail
    
    echo "User Script v1.0"
    echo "================"
    echo ""
    
    echo "Environment: ${cfg.environment}"
    echo "Encryption method: ${cfg.encryptionMethod}"
    echo ""
    
    # Check if secrets are available
    if [[ -f "${config.sops.secrets."api_key".path}" ]]; then
      API_KEY=$(cat ${config.sops.secrets."api_key".path})
      echo "✅ API key loaded from secrets"
    else
      echo "⚠️  No API key found, using default"
      API_KEY="default-api-key"
    fi
    
    if [[ -f "${config.sops.secrets."db_password".path}" ]]; then
      DB_PASSWORD=$(cat ${config.sops.secrets."db_password".path})
      echo "✅ Database password loaded from secrets"
    else
      echo "⚠️  No database password found, using default"
      DB_PASSWORD="default-db-password"
    fi
    
    if [[ -f "${config.sops.secrets."jwt_secret".path}" ]]; then
      JWT_SECRET=$(cat ${config.sops.secrets."jwt_secret".path})
      echo "✅ JWT secret loaded from secrets"
    else
      echo "⚠️  No JWT secret found, using default"
      JWT_SECRET="default-jwt-secret"
    fi
    
    # Main script logic
    case "''${1:-help}" in
      backup)
        echo "Running backup with token: [REDACTED]"
        echo "Backing up to: ''${cfg.backupPath}"
        # Backup logic here
        ;;
      
      sync)
        echo "Running sync with configuration"
        echo "Sync interval: ''${cfg.syncInterval} minutes"
        # Sync logic here
        ;;
      
      status)
        echo "Service Status:"
        echo "- Backup path: ''${cfg.backupPath}"
        echo "- Sync interval: ''${cfg.syncInterval} minutes"
        echo "- Secrets: Configured"
        ;;
      
      help|*)
        echo "Usage: user-script [command]"
        echo ""
        echo "Commands:"
        echo "  backup  - Run backup operation"
        echo "  sync    - Synchronize data"
        echo "  status  - Show configuration status"
        echo "  help    - Show this help"
        ;;
    esac
  '';
in
{
  options.programs.user-script = {
    enable = mkEnableOption "User-executable script with sops";
    
    backupPath = mkOption {
      type = types.path;
      default = "/var/backup";
      description = "Path for backup storage";
    };
    
    syncInterval = mkOption {
      type = types.int;
      default = 60;
      description = "Sync interval in minutes";
    };
    
    secretsFile = mkOption {
      type = types.path;
      default = ./secrets/app.yaml;
      description = "Path to encrypted secrets file";
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
    
    timer = {
      enable = mkEnableOption "Enable systemd timer for periodic execution";
      
      onCalendar = mkOption {
        type = types.str;
        default = "hourly";
        description = "Systemd timer schedule (OnCalendar)";
      };
    };
  };
  
  config = mkIf cfg.enable {
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
      owner = "root";
      group = "users";
      mode = "0440";  # Readable by users group
    };
    
    sops.secrets."db_password" = {
      sopsFile = cfg.secretsFile;
      owner = "root";
      group = "users";
      mode = "0440";
    };
    
    sops.secrets."jwt_secret" = {
      sopsFile = cfg.secretsFile;
      owner = "root";
      group = "users";
      mode = "0440";
    };
    
    # Install the script
    environment.systemPackages = [ userScript ];
    
    # Optional: Create systemd timer for periodic execution
    systemd.timers.user-script = mkIf cfg.timer.enable {
      description = "User script periodic execution";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = cfg.timer.onCalendar;
        Persistent = true;
      };
    };
    
    systemd.services.user-script = mkIf cfg.timer.enable {
      description = "User script execution";
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${userScript}/bin/user-script backup";
        User = "nobody";
        Group = "users";
      };
    };
    
    # Create backup directory
    systemd.tmpfiles.rules = [
      "d ${cfg.backupPath} 0755 root users -"
    ];
  };
}