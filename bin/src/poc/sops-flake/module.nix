{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.sops-app;
in
{
  options.services.sops-app = {
    enable = mkEnableOption "Self-contained sops application";

    # Age key configuration (Secret-First approach)
    ageKeyFile = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Path to age key file for sops decryption. Uses system default if null.";
    };
    
    user = mkOption {
      type = types.str;
      default = "sops-app";
      description = "User to run the service as";
    };
    
    group = mkOption {
      type = types.str;
      default = "sops-app";
      description = "Group to run the service as";
    };
  };

  config = mkIf cfg.enable {
    # Secret-First: Age-only configuration (no SSH fallback)
    sops.age.keyFile = mkIf (cfg.ageKeyFile != null) cfg.ageKeyFile;
    
    # Application-specific secrets (unchanged)
    sops.secrets."api-key" = {
      sopsFile = ./secrets/app.yaml;
      owner = cfg.user;
      group = cfg.group;
    };
    
    sops.secrets."db-password" = {
      sopsFile = ./secrets/app.yaml;
      owner = cfg.user;
      group = cfg.group;
    };

    # Create service user
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.group;
    };
    users.groups.${cfg.group} = {};

    # systemd service
    systemd.services.sops-app = {
      description = "Application with sops-managed secrets";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Group = cfg.group;
        EnvironmentFile = [
          config.sops.secrets."api-key".path
          config.sops.secrets."db-password".path
        ];
        ExecStart = "${pkgs.bash}/bin/bash -c 'echo App running with secrets; sleep infinity'";
        Restart = "always";
      };
    };

    # Secret-First: .sops.yaml should be managed by nix run .#secrets-init
    # No automatic generation to prevent SSH fallback usage
  };
}
