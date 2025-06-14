function search_binded() {
    # bind -X と bind -p の出力を結合
    {
        echo "----- bind -X -----"
        bind -X
        echo "----- bind -p -----"
        bind -p
    } | fzf --preview 'echo {}'
}

bind -x '"\C-f\C-b": search_binded'
