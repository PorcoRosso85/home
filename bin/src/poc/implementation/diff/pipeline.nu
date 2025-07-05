#!/usr/bin/env nu

# Integration pipeline for requirement coverage analysis
# Combines kuzu_query, diff, and search tools

def main [] {
    # Always show README.md for default command
    let readme_path = $"($env.FILE_PWD)/README.md"
    if ($readme_path | path exists) {
        open $readme_path | print
    } else {
        # Try compressed version
        let compressed_path = $"($env.FILE_PWD)/README_COMPRESSED.md"
        if ($compressed_path | path exists) {
            open $compressed_path | print
        } else {
            print -e "Error: README.md not found"
            exit 1
        }
    }
}

# Actual pipeline implementation
def "main analyze" [
    path: string                    # Project directory to analyze
    --db-path: string = ""         # KuzuDB path (optional)
    --show-symbols                 # Include symbol information for unspecified files
] {
    let search_path = ([$env.HOME, "bin/src/poc/implementation/search"] | path join)
    
    # Step 1: Query LocationURIs from KuzuDB
    print "📊 Querying KuzuDB for requirements..."
    let kuzu_script = $"($env.FILE_PWD)/kuzu_query.py"
    let uris = if $db_path == "" {
        ^python $kuzu_script | complete
    } else {
        ^python $kuzu_script $db_path | complete
    }
    
    if $uris.exit_code != 0 {
        print -e "Error querying KuzuDB:"
        print -e $uris.stderr
        exit 1
    }
    
    # Step 2: Compare with filesystem
    print "🔍 Comparing requirements with implementation..."
    let diff_script = $"($env.FILE_PWD)/diff.nu"
    let diff_result = $uris.stdout | nu $diff_script $path | from json
    
    # Step 3: Optionally enrich with symbol information
    let enriched_result = if $show_symbols {
        print "🔎 Analyzing symbols in unspecified files..."
        
        $diff_result | each { |item|
            if $item.implementation_exists and not $item.requirement_exists {
                # Get symbols for unspecified files
                let symbol_result = (
                    cd $search_path; nix run . -- $item.path | from json
                )
                
                # Add symbol summary
                $item | merge {
                    symbols_count: ($symbol_result.symbols | length)
                    symbol_types: ($symbol_result.symbols | 
                        group-by type | 
                        transpose key value | 
                        each { |g| {($g.key): ($g.value | length)} } |
                        reduce -f {} { |it, acc| $acc | merge $it }
                    )
                }
            } else {
                $item
            }
        }
    } else {
        $diff_result
    }
    
    # Step 4: Generate summary
    let missing_count = ($enriched_result | where { |item| $item.requirement_exists and not $item.implementation_exists } | length)
    let unspecified_count = ($enriched_result | where { |item| $item.implementation_exists and not $item.requirement_exists } | length)
    
    print ""
    print "📈 Summary:"
    print $"  Missing implementations: ($missing_count)"
    print $"  Unspecified files: ($unspecified_count)"
    
    if $show_symbols {
        let total_symbols = ($enriched_result | 
            where { |item| $item.implementation_exists and not $item.requirement_exists } | 
            get symbols_count | 
            math sum
        )
        print $"  Total symbols in unspecified files: ($total_symbols)"
    }
    
    # Output full results as JSON
    print ""
    print "📋 Detailed results:"
    $enriched_result | to json
}

# Helper command to show only requirement-only files (missing implementation)
export def "main analyze req_only" [
    path: string
    --db-path: string = ""
] {
    main analyze $path --db-path $db_path | 
    from json | 
    where { |item| $item.requirement_exists and not $item.implementation_exists } | 
    get path
}

# Helper command to show only implementation-only files (unspecified in requirements)
export def "main analyze impl_only" [
    path: string
    --db-path: string = ""
] {
    main analyze $path --db-path $db_path | 
    from json | 
    where { |item| $item.implementation_exists and not $item.requirement_exists } | 
    get path
}