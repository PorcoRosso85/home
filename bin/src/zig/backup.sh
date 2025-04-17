#!/bin/bash

backup_files() {
    local backup_dir=$1
    local exclude_dirs=${2#--exclude=}  # --exclude=を除去
    
    if [ -z "$backup_dir" ]; then
        echo "バックアップ先のディレクトリを指定してください。"
        return 1
    fi

    # ディレクトリが存在しない場合、作成するか確認
    if [ ! -d "$backup_dir" ]; then
        echo "指定されたディレクトリが存在しません: $backup_dir"
        read -p "ディレクトリを作成しますか？ (y/n): " create_dir
        if [[ "$create_dir" =~ ^[Yy]$ ]]; then
            mkdir -p "$backup_dir" || { echo "ディレクトリの作成に失敗しました。"; exit 1; }
            echo "ディレクトリを作成しました: $backup_dir"
        else
            echo "ディレクトリが存在しないため、バックアップを中止します。"
            exit 1
        fi
    fi

    # 一時ディレクトリの作成
    temp_dir=$(mktemp -d) || { echo "一時ディレクトリの作成に失敗しました。"; exit 1; }

    # エラーハンドリング
    trap 'rollback' ERR INT TERM

    # バックアップ前に既存のファイルを一時ディレクトリに移動
    if [ -d "$backup_dir/$(basename "$(pwd)")" ]; then
        mv "$backup_dir/$(basename "$(pwd)")" "$temp_dir/" || { echo "既存バックアップの移動に失敗しました"; exit 1; }
    fi

    # rsyncの除外オプションを構築
    rsync_exclude=""
    if [ -n "$exclude_dirs" ]; then
        IFS=',' read -r -a dirs <<< "$exclude_dirs"
        for dir in "${dirs[@]}"; do
            if [ ! -d "$dir" ]; then
                echo "エラー: 除外ディレクトリ '$dir' が存在しません"
                exit 1
            fi
            rsync_exclude+=" --exclude=${dir}"
        done
    fi

    # バックアップ実行
    echo "バックアップを開始します..."
    echo "現在のディレクトリ: $(pwd)"
    echo "バックアップ先: $backup_dir"
    
    # 大きなファイルを表示
    echo -e "\n大きなファイルを検出中..."
    find . -type f -size +100M -exec ls -lh {} \; | awk '{print $5,$9}' || true
    echo ""
    
    # 進捗表示用の関数
    show_progress() {
        local total_files=$(find . -type f | wc -l)
        local processed_files=0
        local start_time=$(date +%s)
        
        echo "総ファイル数: $total_files"
        
        while read -r line; do
            processed_files=$((processed_files + 1))
            local current_time=$(date +%s)
            local elapsed=$((current_time - start_time))
            local remaining=$(( (total_files - processed_files) * elapsed / processed_files ))
            
            echo -ne "\r処理中... $processed_files/$total_files ファイル ($((processed_files * 100 / total_files))%) "
            printf "経過時間: %02d:%02d 残り時間: %02d:%02d" \
                $((elapsed/60)) $((elapsed%60)) \
                $((remaining/60)) $((remaining%60))
        done < <(rsync -a --info=progress2 $rsync_exclude . "$backup_dir/")
        
        echo -e "\n"
    }

    if ! show_progress; then
        echo "バックアップに失敗しました"
        rollback
        exit 1
    fi
    
    echo "バックアップ完了: $(pwd) -> $backup_dir"
    echo "所要時間: $(( ($(date +%s) - start_time) / 60 ))分$(( ($(date +%s) - start_time) % 60 ))秒"
    
    echo "バックアップ完了: $(pwd) -> $backup_dir"
    if [ -n "$exclude_dirs" ]; then
        echo "除外ディレクトリ: $exclude_dirs"
    fi

    # 一時ディレクトリを削除
    rm -rf "$temp_dir"
}

rollback() {
    echo "エラーが発生しました。ロールバックを実行します。"
    if [ -d "$temp_dir/$(basename "$(pwd)")" ]; then
        mv "$temp_dir/$(basename "$(pwd)")" "$backup_dir/" || echo "ロールバックに失敗しました"
    fi
    rm -rf "$temp_dir"
    exit 1
}

# 引数解析
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <バックアップ先ディレクトリ> [--exclude=dir1,dir2,...]"
    exit 1
fi

if [ $# -eq 2 ]; then
    if [[ "$2" == --exclude=* ]]; then
        backup_files "$1" "$2"
    else
        echo "エラー: 不明なオプション '$2'"
        echo "有効なオプションは --exclude=dir1,dir2,... のみです"
        exit 1
    fi
else
    backup_files "$1"
fi
