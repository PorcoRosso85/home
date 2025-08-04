# Shell Script Categorization

## Core Infrastructure
**main.sh**
- Central bash configuration hub
- Auto-sources all shell scripts
- Manages prompt, colors, history, completion
- Dependencies: dircolors, lesspipe, tput, notify-send, hx, nix shell

## Tmux Session Management
**aa.sh**
- Basic tmux workspace (shell + watch)
- Directory-based session naming

**hly.sh**
- Development tmux workspace (helix + lazygit + yazi)
- Directory-based session naming

## Search & Discovery
**search_binded_keys.sh**
- Interactive key binding search (Ctrl+F Ctrl+B)
- Dependencies: bind, fzf

**search_declared_functions.sh**
- Interactive function search (Ctrl+F Ctrl+F)
- Dependencies: declare, fzf

## Development Utilities
**todo.sh**
- Development workflow tools (ff, fw, cmdf, jq_, gloj)
- Dependencies: fzf, fd, bat, grep, jq, git, nvim

**cat_fzf.sh**
- Interactive file viewer (Ctrl+F)
- Dependencies: fzf, cat

## System Management
**backup_files.sh**
- Automated dotfile backup
- Dependencies: rsync, mktemp

**build_home_by_nix.sh**
- Home-manager build wrapper
- Dependencies: nix

## Configuration
**aichat.sh**
- AI chat tool environment variables
- No executable code, pure configuration

## Migration Priority
1. **Critical**: main.sh (central hub)
2. **High**: search scripts, tmux managers
3. **Medium**: utilities (todo.sh, cat_fzf.sh)
4. **Low**: standalone tools (backup, build, aichat config)