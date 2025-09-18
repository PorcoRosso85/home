# SystemD Web API Example

A simple web API service running as a systemd service with sops-nix secret management.

## Features
- Runs as systemd service
- Reads encrypted API key from sops
- Automatic service restart on failure
- Dedicated service user

## Setup

### 1. Generate age key
```bash
age-keygen -o ~/.config/sops/age/keys.txt
```

### 2. Update .sops.yaml
Replace the example age public key with your actual public key.

### 3. Encrypt secrets
```bash
sops -e secrets/app.yaml > secrets/app.yaml.enc
mv secrets/app.yaml.enc secrets/app.yaml
```

### 4. Deploy to NixOS

Add to your NixOS configuration:
```nix
{
  imports = [
    ./path/to/systemd-web-api/module.nix
  ];
  
  services.sops-web-api = {
    enable = true;
    port = 8080;
  };
  
  # Enable sops-nix
  sops.defaultSopsFile = ./secrets/app.yaml;
  sops.age.keyFile = "/var/lib/sops-nix/key.txt";
}
```

### 5. Test the service
```bash
# Check service status
systemctl status sops-web-api

# Test the API
curl http://localhost:8080
```

## Service Details
- **User**: web-api (system user)
- **Port**: 8080 (configurable)
- **Restart**: Always with 5s delay
- **Dependencies**: network.target, sops-nix.service