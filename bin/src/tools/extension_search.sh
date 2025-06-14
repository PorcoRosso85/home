#!/usr/bin/env bash
set -e

# @describe テキスト検索ツール - ファイルやディレクトリ内でテキストパターンを検索します
# @option --pattern! 検索するテキストパターン（正規表現使用可）
# @option --path ディレクトリパス (デフォルト: カレントディレクトリ)
# @option --file-pattern 検索対象のファイルパターン（例: "*.txt", "*.{js,ts}"）
# @flag --case-sensitive 大文字と小文字を区別する
# @flag --only-filenames ファイル名のみを表示する
# @flag --fuzzy ファジーマッチングを有効にする（単語の間に任意文字を許容）
# @flag --show-help マッチしたファイルの -h/--help 出力も表示する

# @env LLM_OUTPUT=/dev/stdout 出力先

# argc評価を先に実行
eval "$(argc --argc-eval "$0" "$@")"

ROOT_DIR="${LLM_ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/..}" && pwd)}"

# デフォルト値の設定
pattern="${argc_pattern}"
path="${argc_path:-.}"
file_pattern="${argc_file_pattern:-*}"
case_sensitive="${argc_case_sensitive:-false}"
only_filenames="${argc_only_filenames:-false}"
fuzzy="${argc_fuzzy:-false}"
show_help="${argc_show_help:-false}"

# 出力開始
{
    # デバッグ情報の出力
    echo "🔧 デバッグ情報:"
    echo "- パス: $path"
    echo "- ファイルパターン: $file_pattern"
    echo "- 大文字小文字区別: $case_sensitive"
    echo "- ファイル名のみ: $only_filenames"
    echo "- ファジーマッチング: $fuzzy"
    echo "- ヘルプを表示: $show_help"
    echo ""
    
    # ファジーマッチングの処理
    if [ "$fuzzy" = "1" ] || [ "$fuzzy" = "true" ]; then
        echo "🔍 ファジーマッチングが有効です"
        # 簡易的なファジーマッチング：パターンを `.*(文字).*` の形式に変換
        fuzzy_pattern=""
        for (( i=0; i<${#pattern}; i++ )); do
            fuzzy_pattern="${fuzzy_pattern}.*${pattern:$i:1}"
        done
        fuzzy_pattern="${fuzzy_pattern}.*"
        
        pattern="$fuzzy_pattern"
        echo "🔍 変換後パターン: \"$pattern\""
    else
        echo "💡 ファジーマッチングは無効です。有効にするには --fuzzy フラグを使用してください。"
    fi
    
    echo "🔍 パターン \"$pattern\" を検索中..."
    
    # 大文字小文字の区別
    grep_options="-E"  # 拡張正規表現を使用
    if [ "$case_sensitive" = "false" ]; then
        grep_options="$grep_options -i"
    fi
    
    # ファイル名のみ表示オプション
    if [ "$only_filenames" = "true" ]; then
        grep_options="$grep_options -l"
    fi
    
    # 検索実行とファイル一覧取得
    if [ -d "$path" ]; then
        if [ "$only_filenames" = "true" ]; then
            matching_files=$(find "$path" -type f -name "$file_pattern" -exec grep -l $grep_options "$pattern" {} \; 2>/dev/null)
            
            if [ -z "$matching_files" ]; then
                echo "❌ 検索パターン \"$pattern\" にマッチするものは見つかりませんでした。"
            else
                echo "✅ 検索結果:"
                echo "$matching_files"
                
                # ヘルプ表示が有効な場合
                if [ "$show_help" = "1" ] || [ "$show_help" = "true" ]; then
                    echo ""
                    echo "📚 マッチしたファイルのヘルプ情報:"
                    echo ""
                    
                    # 各ファイルのヘルプ情報を取得
                    for file in $matching_files; do
                        if [ -x "$file" ]; then  # 実行可能ファイルのみ
                            echo "==== $file のヘルプ情報 ===="
                            # ヘルプ出力を試行（-h, --help の順で試す）
                            help_output=$("$file" -h 2>&1 || "$file" --help 2>&1 || echo "ヘルプ情報がありません")
                            echo "$help_output"
                            echo ""
                        fi
                    done
                fi
            fi
        else
            result=$(find "$path" -type f -name "$file_pattern" -exec grep -n $grep_options "$pattern" {} \; 2>/dev/null)
            
            if [ -z "$result" ]; then
                echo "❌ 検索パターン \"$pattern\" にマッチするものは見つかりませんでした。"
            else
                echo "✅ 検索結果:"
                echo "$result"
                
                # ヘルプ表示が有効な場合
                if [ "$show_help" = "1" ] || [ "$show_help" = "true" ]; then
                    echo ""
                    echo "📚 マッチしたファイルのヘルプ情報:"
                    echo ""
                    
                    # 結果からユニークなファイル名を抽出
                    # grep結果の形式: ファイル名:行番号:内容
                    matching_files=$(echo "$result" | sed 's/:.*//' | sort -u)
                    
                    # 各ファイルのヘルプ情報を取得
                    for file in $matching_files; do
                        if [ -x "$file" ]; then  # 実行可能ファイルのみ
                            echo "==== $file のヘルプ情報 ===="
                            # ヘルプ出力を試行（-h, --help の順で試す）
                            help_output=$("$file" -h 2>&1 || "$file" --help 2>&1 || echo "ヘルプ情報がありません")
                            echo "$help_output"
                            echo ""
                        fi
                    done
                fi
            fi
        fi
    else
        echo "❌ 指定されたパス \"$path\" は存在しないか、ディレクトリではありません。"
        exit 1
    fi
} > "$LLM_OUTPUT"
