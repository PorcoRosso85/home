#! /bin/bash
search_bash_histories() {
    local output
    output=$(HISTTIMEFORMAT= history | 
        awk '{$1=""; print substr($0,2)}' |
        fzf --height ${FZF_TMUX_HEIGHT:-40%} $FZF_DEFAULT_OPTS -n2..,.. --tiebreak=index --bind=ctrl-r:toggle-sort $FZF_CTRL_R_OPTS --query="$READLINE_LINE" +m)
    READLINE_LINE=${output}
    READLINE_POINT=${#READLINE_LINE}
}

bind -x '"\C-r": search_bash_histories'
