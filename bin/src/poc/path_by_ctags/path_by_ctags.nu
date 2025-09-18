#!/usr/bin/env nu

# ctagsを使用してシンボルを検索
export def find-symbols [
    directory: path      # 検索対象ディレクトリ
    --pattern (-p): string = ""  # シンボルパターン
    --ext (-e): string = "py"    # ファイル拡張子
] {
    # 一時ファイルを作成
    let tags_file = (mktemp -t tags.XXXXXX)
    
    # ctagsを実行
    try {
        ^ctags -f $tags_file -R --fields=+n $"--langmap=python:+.($ext)" $directory
    } catch {
        rm -f $tags_file
        error make {msg: $"Failed to generate ctags: ($in)"}
    }
    
    # tagsファイルを解析
    let symbols = (
        open $tags_file 
        | lines 
        | where { |line| not ($line | str starts-with "!") }
        | each { |line|
            let parts = ($line | split column "\t")
            if ($parts | length) < 4 {
                return null
            }
            
            let symbol = ($parts | get column1.0)
            let file_path = ($parts | get column2.0)
            let ex_cmd = ($parts | get column3.0)
            
            # 行番号を抽出
            let line_num = (
                $parts
                | skip 3
                | each { |field| $field | get column1 }
                | where { |f| $f | str starts-with "line:" }
                | first
                | default ""
                | str replace "line:" ""
                | into int
                | default 0
            )
            
            # タイプを判定
            let symbol_type = if ($ex_cmd | str contains "class ") {
                "class"
            } else if ($ex_cmd | str contains "def ") {
                "function"
            } else {
                "unknown"
            }
            
            {
                name: $symbol
                file: $file_path
                line: $line_num
                type: $symbol_type
            }
        }
        | compact
    )
    
    # クリーンアップ
    rm -f $tags_file
    
    # フィルタリング
    if $pattern != "" {
        $symbols | where { |s| $s.name | str contains $pattern }
    } else {
        $symbols
    }
    | sort-by file line
}

# JSON出力用のラッパー
export def find-symbols-json [
    directory: path
    --pattern (-p): string = ""
    --ext (-e): string = "py"
] {
    find-symbols $directory --pattern $pattern --ext $ext | to json
}

# メイン関数
export def main [
    directory: path      # 検索対象ディレクトリ
    --pattern (-p): string = ""  # シンボルパターン
    --ext (-e): string = "py"    # ファイル拡張子
    --json (-j)                  # JSON出力
] {
    let results = find-symbols $directory --pattern $pattern --ext $ext
    
    if $json {
        $results | to json
    } else {
        $results | each { |s| 
            $"($s.name | fill -a l -w 30) ($s.type | fill -a l -w 10) ($s.file):($s.line)"
        } | str join "\n"
    }
}