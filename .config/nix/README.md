# Home Manager Configuration

## Setup

### New environment
```bash
git clone <repo> ~/
cd ~/.config/nix
nix build
./result/activate
```

### Apply changes
```bash
cd ~/.config/nix
nix build && ./result/activate
```

## Current Configuration

- **Shell**: bash with custom config, starship prompt
- **Development**: nodejs_22, pnpm, python3.11, uv, go, rust
- **Tools**: ripgrep, fzf, fd, bat, eza, zoxide, broot
- **Nix tools**: nixd, nixfmt-rfc-style

## Structure
```
~/.config/nix/
├── flake.nix       # Entry point
├── home.nix        # Main configuration
└── modules/        # Modular configs
    └── packages.nix
```

## Without clone (direct from GitHub)
```bash
# From default branch
nix build github:yourusername/yourrepo#homeConfigurations.nixos.activationPackage
./result/activate

# From specific branch
nix build github:yourusername/yourrepo/<branchName>#homeConfigurations.nixos.activationPackage
./result/activate
```

## Alternative setup (partial clone)
```bash
git init
git remote add origin https://github.com/yourusername/yourrepo.git
git fetch origin <branchName>
git checkout <branchName> -- .config/nix
cd .config/nix
nix build
./result/activate
```