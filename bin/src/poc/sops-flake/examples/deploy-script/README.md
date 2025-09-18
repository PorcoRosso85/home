# Deploy Script Example

Secure deployment script with encrypted secrets and configuration.

## Features
- Environment-specific encrypted configurations
- Encrypted shell script execution (sops exec-file)
- Separate public and sensitive operations
- Multiple deployment actions (deploy, rollback, status)

## Setup

### 1. Initialize secrets
```bash
nix run .#setup-secrets
```

This creates:
- Age encryption key
- Sample configuration files for staging/production
- Sample encrypted deployment script

### 2. Encrypt configurations
```bash
# Encrypt staging configuration
sops -e secrets/deploy-staging.plain.yaml > secrets/deploy-staging.yaml

# Encrypt production configuration  
sops -e secrets/deploy-production.plain.yaml > secrets/deploy-production.yaml

# Encrypt deployment script
sops -e secrets/deploy.sh > secrets/deploy.sh.enc

# Clean up plain files
rm secrets/*.plain.yaml secrets/deploy.sh
```

### 3. Usage

#### Deploy to staging
```bash
nix run . -- staging deploy
```

#### Check production status
```bash
nix run . -- production status
```

#### Rollback staging deployment
```bash
nix run . -- staging rollback
```

## Configuration Structure

### Server Configuration (deploy-{env}.yaml)
```yaml
server:
  host: example.com
  port: 22
  user: deploy
paths:
  source: /var/www/app
  backup: /var/backups/app
credentials:
  api_key: secret-key
  db_password: secret-pass
```

### Encrypted Script (deploy.sh.enc)
Contains sensitive operations like:
- Database migrations with credentials
- API key configuration
- Secret rotation
- Vault operations

## Architecture

```
┌─────────────────┐
│   deploy.sh     │  Public operations
│   (plaintext)   │  (build, test, validate)
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Deployment Flow │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ deploy.sh.enc   │  Sensitive operations
│  (encrypted)    │  (credentials, secrets)
└─────────────────┘
```

## Security Notes

1. **Never commit plain secrets**: Always encrypt before committing
2. **Age key protection**: Store age private key securely
3. **Environment separation**: Use different keys for different environments
4. **Audit trail**: All deployments are logged
5. **Rollback capability**: Always create backups before deployment

## Environment Variables

- `SECRETS_DIR`: Directory containing encrypted files
- `SOPS_AGE_KEY_FILE`: Path to age private key

## Development

```bash
# Enter development shell
nix develop

# Available tools:
# - sops: Secret encryption
# - age: Key management
# - jq/yq: JSON/YAML processing
# - rsync: File synchronization
# - openssh: SSH operations
```

## Testing

```bash
# Test deployment without actual connection
TARGET=staging ACTION=deploy nix run .

# Verify configuration decryption
sops -d secrets/deploy-staging.yaml

# Test encrypted script execution
sops exec-file secrets/deploy.sh.enc 'bash {}'
```