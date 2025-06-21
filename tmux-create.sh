#!/bin/bash

# tmux新規セッション作成スクリプト

# 現在のセッションを記録
CURRENT_SESSION=$(tmux display-message -p '#S' 2>/dev/null)

# キャッシュファイルの設定
CACHE_FILE="$HOME/.tmux-git-repos-cache"
CACHE_AGE=1 # 1日でキャッシュ更新

# キャッシュが古いか存在しない場合は更新
if [ ! -f "$CACHE_FILE" ] || [ -n "$(find "$CACHE_FILE" -mtime +$CACHE_AGE 2>/dev/null)" ]; then
    echo "Updating Git repository cache..." >&2
    
    # 1. fd (最速) がある場合
    if command -v fd &> /dev/null; then
        fd -H -t d '^\.git$' ~ -x dirname {} | sort -u > "$CACHE_FILE"
    # 2. git ls-files を使う方法（高速だが既知のリポジトリのみ）
    elif command -v git &> /dev/null; then
        {
            # 既知のGitリポジトリを高速検索
            git config --global --get-regexp '^remote\..*\.url$' 2>/dev/null | \
                while read -r key url; do
                    repo_path=$(echo "$key" | sed 's/^remote\.\(.*\)\.url$/\1/')
                    [ -d "$HOME/$repo_path/.git" ] && echo "$HOME/$repo_path"
                done
            # findでも補完検索（浅い階層のみ）
            find ~ -maxdepth 3 -type d -name ".git" 2>/dev/null | sed 's|/.git||'
        } | sort -u > "$CACHE_FILE"
    # 3. findのみ（最も遅い）
    else
        find ~ -maxdepth 4 -type d -name ".git" 2>/dev/null | \
            sed 's|/.git||' | \
            grep -v "node_modules\|\.cache\|\.local\|\.npm\|\.cargo" | \
            sort -u > "$CACHE_FILE"
    fi
fi

# キャッシュからfzfで選択
SELECTED_DIR=$(cat "$CACHE_FILE" | \
    fzf --height=20 --layout=reverse --border \
        --header="Select Git repository: (ESC to cancel)" \
        --preview 'echo "📁 $(basename {})"; echo "📍 {}"; echo; git -C {} log --oneline -5 --graph 2>/dev/null; echo; git -C {} status -sb 2>/dev/null' \
        --preview-window=right:60%)

# ディレクトリが選択された場合
if [ -n "$SELECTED_DIR" ]; then
    cd "$SELECTED_DIR"
    
    # Gitブランチを取得
    GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
    SESSION_NAME="$(basename "$SELECTED_DIR")-${GIT_BRANCH}"
    
    # セッションが既に存在するか確認
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "Session '$SESSION_NAME' already exists. Attaching..."
        tmux attach-session -t "$SESSION_NAME"
    else
        # 新規セッション作成（tmux.shの設定を適用）
        cd "$SELECTED_DIR" && bash $HOME/tmux.sh
    fi
elif [ -n "$CURRENT_SESSION" ]; then
    # キャンセルした場合、元のセッションに戻る
    tmux attach-session -t "$CURRENT_SESSION"
else
    echo "No directory selected."
fi