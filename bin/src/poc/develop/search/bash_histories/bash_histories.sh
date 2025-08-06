#!/usr/bin/env bash
# bash_histories.sh - Simple bash history search without flake evaluation
# Designed to be called with: nix shell nixpkgs#fzf --command bash bash_histories.sh

# Exit if no bash history
if [ ! -f ~/.bash_history ]; then
    echo "No bash history file found" >&2
    exit 1
fi

# Search bash history with fzf
tac ~/.bash_history | 
awk '!seen[$0]++' | 
fzf --height ${FZF_TMUX_HEIGHT:-40%} $FZF_DEFAULT_OPTS -n2..,.. --tiebreak=index --bind=ctrl-r:toggle-sort $FZF_CTRL_R_OPTS --query="$READLINE_LINE" +m