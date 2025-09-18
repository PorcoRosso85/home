# NixOS System Configuration

## Directory Structure

```
~/.os/
├── flake.nix              # Main flake configuration
├── hosts/
│   └── nixos-vm/         # VM-specific configuration
│       ├── default.nix
│       └── hardware-configuration.nix
├── modules/
│   ├── common.nix        # Common system configuration
│   └── secrets.nix       # SOPS secrets management
├── hardware-configuration.nix  # Legacy hardware config
└── configuration.nix           # Legacy system config
```

## Setup

### From remote repository
```bash
# Direct from GitHub (no clone needed)
sudo nixos-rebuild switch --flake github:yourusername/yourrepo#nixos-vm

# From specific branch
sudo nixos-rebuild switch --flake github:yourusername/yourrepo/<branchName>#nixos-vm
```

### With local clone
```bash
git clone <repo> ~/.os
cd ~/.os
sudo nixos-rebuild switch --flake .#nixos-vm
```

## Staged Verification Process

Before applying system changes, follow these verification steps:

### 1. Build Configuration
```bash
cd ~/.os
sudo nixos-rebuild build --flake ~/.os#nixos-vm
```
This builds the configuration without applying it, allowing you to catch build errors early.

### 2. Check Changes
```bash
nix store diff-closures /run/current-system ./result
```
This shows what packages will be added, removed, or updated.

### 3. Dry Run Activation
```bash
sudo nixos-rebuild dry-activate --flake ~/.os#nixos-vm
```
This simulates the activation process and shows what systemd units would be restarted.

### 4. Test Configuration
```bash
sudo nixos-rebuild test --flake ~/.os#nixos-vm
```
This applies the configuration temporarily (until reboot) for testing.

### 5. Apply Permanently
```bash
sudo nixos-rebuild switch --flake ~/.os#nixos-vm
```
This makes the configuration permanent and adds it to the boot menu.

### 6. Rollback if needed
```bash
sudo nixos-rebuild switch --rollback
```
This rolls back to the previous generation if something goes wrong.

## Quick Apply (for trusted changes)
```bash
cd ~/.os
sudo nixos-rebuild switch --flake .#nixos-vm
```

## Current Configuration

- **Host**: nixos-vm (modular VM configuration)
- **Packages**: git, helix, yazi, lazygit, etc.
- **Features**: sops-nix secrets management
- **Architecture**: Modular design with host-specific and common modules

## Flake inputs
- nixpkgs (25.05)
- nixpkgs-unstable
- sops-nix

## Migration Notes
- WSL and vscode-server modules are temporarily disabled for structural separation
- Legacy configuration.nix and hardware-configuration.nix files are preserved but unused
- Host-specific configurations are now in `hosts/nixos-vm/`