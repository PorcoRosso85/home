# CLI Tool Example

A standalone CLI application with SOPS-managed configuration.

## Features
- Encrypted configuration management
- Multiple commands (process, config, encrypt-config)
- Environment variable support
- Self-contained with all dependencies

## Quick Start

### 1. Initialize configuration
```bash
nix run .#init-config
```

This will:
- Generate an age key (if not exists)
- Create .sops.yaml with your public key
- Generate a sample configuration file

### 2. Encrypt your configuration
```bash
# Edit the plain configuration
vim secrets/config.plain.yaml

# Encrypt it
sops -e secrets/config.plain.yaml > secrets/config.yaml

# Remove the plain file
rm secrets/config.plain.yaml
```

### 3. Run the CLI tool
```bash
# Using nix run
nix run . -- process "Hello World"

# View configuration
nix run . -- config

# Show help
nix run . -- help
```

## Installation

### As a Nix package
```bash
nix build .
./result/bin/sops-cli-tool help
```

### In NixOS configuration
```nix
{
  environment.systemPackages = [
    (import ./path/to/cli-tool {})
  ];
}
```

## Commands

### `process <data>`
Process data using the encrypted configuration.
```bash
sops-cli-tool process "My data to process"
```

### `config`
Display the current decrypted configuration.
```bash
sops-cli-tool config
```

### `encrypt-config <file>`
Encrypt a plain configuration file.
```bash
sops-cli-tool encrypt-config plain-config.yaml
```

## Environment Variables

- `SECRETS_FILE`: Path to encrypted configuration file
- `SOPS_AGE_KEY_FILE`: Path to age private key (default: ~/.config/sops/age/keys.txt)

## Configuration Structure

```yaml
api:
  endpoint: https://api.example.com
  token: your-secret-token
settings:
  timeout: 30
  retries: 3
  debug: false
features:
  cache: true
  logging: true
```

## Development

Enter development shell:
```bash
nix develop
```

This provides:
- sops: Secret encryption/decryption
- age: Key generation
- jq/yq: JSON/YAML processing