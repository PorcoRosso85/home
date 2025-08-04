#!/usr/bin/env bash
# Search for flake.nix directories and return selected directory

# デフォルトの検索ディレクトリ
search_dir="$HOME"

# JSON入力があるか確認
if [ ! -t 0 ]; then
    # パイプまたはリダイレクトからの入力
    input=$(cat)
    if [ -n "$input" ]; then
        # JSON解析してsearch_dirを取得 (jqが利用可能な場合)
        if command -v jq >/dev/null 2>&1; then
            dir_from_json=$(echo "$input" | jq -r '.search_dir // empty' 2>/dev/null)
            if [ -n "$dir_from_json" ]; then
                search_dir="$dir_from_json"
            fi
        fi
    fi
fi

# 検索実行
if command -v fd >/dev/null 2>&1; then
    files=$(fd -H -t f "flake.nix" "$search_dir" 2>/dev/null || true)
else
    files=$(find "$search_dir" -name "flake.nix" -type f 2>/dev/null || true)
fi

if [ -z "$files" ]; then
    echo "No flake.nix files found" >&2
    exit 1
fi

# ディレクトリリストを作成
dirs=$(echo "$files" | 
    while read -r file; do dirname "$file"; done | 
    sort -u)

# fzfが利用可能かチェック
if command -v fzf >/dev/null 2>&1; then
    # fzfを使用
    selected_dir=$(echo "$dirs" |
        fzf --reverse --header="Select flake directory:" \
            --preview 'ls -la {} 2>/dev/null || echo "Directory not accessible"' \
            --preview-window=right:50%)
else
    # fzfが利用不可能な場合の代替実装
    echo "Available flake directories:" >&2
    echo "$dirs" | nl -nln -w3 >&2
    echo -n "Enter number (or 'q' to quit): " >&2
    read -r selection
    
    if [ "$selection" = "q" ] || [ -z "$selection" ]; then
        exit 1
    fi
    
    # 番号が有効かチェック
    if ! [[ "$selection" =~ ^[0-9]+$ ]]; then
        echo "Invalid selection" >&2
        exit 1
    fi
    
    selected_dir=$(echo "$dirs" | sed -n "${selection}p")
    
    if [ -z "$selected_dir" ]; then
        echo "Invalid selection" >&2
        exit 1
    fi
fi

if [ -n "$selected_dir" ]; then
    echo "$selected_dir"
else
    exit 1
fi