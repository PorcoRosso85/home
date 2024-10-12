#!/bin/bash

function search_declared_functions() {
    # declare -fで関数一覧を取得し、fzfで選択
    local selected_function
    selected_function=$(declare -f | fzf --height 40% --reverse --preview "echo {}" --preview-window=up:30%)

    # # 選択された関数が空でない場合、プロンプトに挿入
    # if [[ -n "$selected_function" ]]; then
    #     # 選択した関数名を抽出
    #     local function_name
    #     function_name=$(echo "$selected_function" | awk '{print \$2}' | tr -d '()')

    #     # プロンプトに関数名を挿入
    #     echo "$function_name"
    # fi
}

bind -x '"\C-f\C-f": search_declared_functions'
