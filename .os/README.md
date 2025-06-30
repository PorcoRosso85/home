# NixOS System Configuration

## Setup

### From remote repository
```bash
# Direct from GitHub (no clone needed)
sudo nixos-rebuild switch --flake github:yourusername/yourrepo#nixos

# From specific branch
sudo nixos-rebuild switch --flake github:yourusername/yourrepo/<branchName>#nixos
```

### With local clone
```bash
git clone <repo> ~/
cd ~/.os
sudo nixos-rebuild switch --flake .
```

### Apply changes
```bash
cd ~/.os
sudo nixos-rebuild switch --flake .
```

## Current Configuration

- **WSL**: Enabled with nixos user
- **Services**: vscode-server, tailscale, dbus
- **Packages**: git, helix, yazi, lazygit, etc.
- **Features**: Docker, tmux, sudo without password

## Flake inputs
- nixpkgs (25.05)
- nixpkgs-unstable
- nixos-wsl
- vscode-server

## VSCode Integration
The nixos-vscode-server module is included for seamless VSCode Remote development.