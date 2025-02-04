
cat_fzf() {
  local file=$(fzf)
  if [ -n "$file" ]; then
    cat "$file"
  fi
}

# Ctrl + Fにバインド
# bind -s '\C-f' 'cat_fzf\n'
bind -x '"\C-f": cat_fzf'
