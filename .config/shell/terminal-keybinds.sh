#!/usr/bin/env bash
# Terminal keybindings for migrated commands

# Ctrl+F Ctrl+B - Search bash key bindings
bind -x '"\C-f\C-b": /home/nixos/bin/src/develop/terminal/search-keys'

# Ctrl+F Ctrl+F - Search declared functions  
bind -x '"\C-f\C-f": /home/nixos/bin/src/develop/terminal/search-functions'

# Ctrl+F - Interactive file selection and display
bind -x '"\C-f": /home/nixos/bin/src/develop/terminal/cat-fzf'