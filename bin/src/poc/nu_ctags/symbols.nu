#!/usr/bin/env nu

# シンボル一覧を取得
export def symbols [
    path: string      # 検索パス
    --ext (-e): string = "py"  # ファイル拡張子
] {
    # パスの検証
    if not ($path | path exists) {
        error make {msg: $"Path '($path)' does not exist"}
    }
    
    let search_path = if ($path | str ends-with "/") { $path } else { $path + "/" }
    let files = glob $"($search_path)**/*.($ext)"
    
    if ($files | is-empty) {
        return []
    }
    
    $files
    | each { |file|
        open $file
        | lines
        | enumerate
        | each { |line|
            let patterns = if $ext == "py" {
                [
                    {type: "function", pattern: "^\\s*def\\s+(\\w+)"},
                    {type: "class", pattern: "^\\s*class\\s+(\\w+)"},
                    {type: "method", pattern: "^\\s+def\\s+(\\w+)"},
                    {type: "variable", pattern: "^(\\w+)\\s*="},
                ]
            } else if $ext == "rs" {
                [
                    {type: "function", pattern: "^\\s*fn\\s+(\\w+)"},
                    {type: "struct", pattern: "^\\s*struct\\s+(\\w+)"},
                    {type: "enum", pattern: "^\\s*enum\\s+(\\w+)"},
                    {type: "impl", pattern: "^\\s*impl\\s+(\\w+)"},
                ]
            } else if $ext in ["js", "ts"] {
                [
                    {type: "function", pattern: "^\\s*function\\s+(\\w+)"},
                    {type: "class", pattern: "^\\s*class\\s+(\\w+)"},
                    {type: "const", pattern: "^\\s*const\\s+(\\w+)"},
                    {type: "let", pattern: "^\\s*let\\s+(\\w+)"},
                ]
            } else {
                []
            }
            
            $patterns
            | each { |p|
                if ($line.item =~ $p.pattern) {
                    let match = ($line.item | parse -r $p.pattern | get capture0?.0? | default "")
                    if $match != "" {
                        {
                            file: $file
                            line: ($line.index + 1)
                            type: $p.type
                            name: $match
                        }
                    }
                }
            }
        }
        | flatten
        | compact
    }
    | flatten
    | sort-by file line
}