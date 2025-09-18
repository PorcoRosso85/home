#!/usr/bin/env bash
# Flake依存関係と責務を抽出する最小限のスクリプト

if [[ ! -f "flake.lock" ]]; then
    echo "Error: flake.lock not found"
    exit 1
fi

# flake.lockから依存関係を解析
jq -r '.nodes | to_entries[] | select(.key != "root") | 
    "\(.key)|\(.value.locked.type // "unknown")|\(
        if .value.locked.type == "path" then 
            .value.locked.path 
        elif .value.locked.type == "github" then 
            "\(.value.locked.owner)/\(.value.locked.repo)" 
        else 
            "unknown" 
        end
    )"' flake.lock | while IFS='|' read -r name type path; do
    
    echo "【$name】"
    echo "タイプ: $type"
    echo "パス: $path"
    
    # 責務（description）の取得
    if [[ "$type" == "path" && -f "$path/flake.nix" ]]; then
        # ローカル：flake.nixから直接
        desc=$(grep -oP '^\s*description\s*=\s*"\K[^"]*' "$path/flake.nix" 2>/dev/null || echo "未設定")
    elif [[ "$type" == "github" ]]; then
        # GitHub：nix flake metadataで取得
        desc=$(nix flake metadata "github:$path" 2>/dev/null | \
               grep -oP 'Description:\s*\K.*' | \
               sed 's/\x1b\[[0-9;]*m//g' | xargs || echo "取得失敗")
    else
        desc="取得不可"
    fi
    
    echo "責務: $desc"
    echo ""
done