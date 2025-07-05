#!/usr/bin/env nu

# Integration pipeline for requirement coverage analysis
# Combines kuzu_query, diff, and search tools

def main [
    path: string                    # Project directory to analyze
    --db-path: string = ""         # KuzuDB path (optional)
    --show-symbols: bool = false   # Include symbol information for unspecified files
] {
    let search_path = ([$env.HOME, "bin/src/poc/implementation/search"] | path join)
    
    # Step 1: Query LocationURIs from KuzuDB
    print "📊 Querying KuzuDB for requirements..."
    let uris = if $db_path == "" {
        ^python kuzu_query.py | complete
    } else {
        ^python kuzu_query.py $db_path | complete
    }
    
    if $uris.exit_code != 0 {
        print -e "Error querying KuzuDB:"
        print -e $uris.stderr
        exit 1
    }
    
    # Step 2: Compare with filesystem
    print "🔍 Comparing requirements with implementation..."
    let diff_result = $uris.stdout | nu diff.nu $path | from json
    
    # Step 3: Optionally enrich with symbol information
    let enriched_result = if $show_symbols {
        print "🔎 Analyzing symbols in unspecified files..."
        
        $diff_result | each { |item|
            if $item.status == "unspecified" {
                # Get symbols for unspecified files
                let symbol_result = (
                    cd $search_path
                    nix run . -- $item.path | from json
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
    let missing_count = ($enriched_result | where status == "missing" | length)
    let unspecified_count = ($enriched_result | where status == "unspecified" | length)
    
    print ""
    print "📈 Summary:"
    print $"  Missing implementations: ($missing_count)"
    print $"  Unspecified files: ($unspecified_count)"
    
    if $show_symbols {
        let total_symbols = ($enriched_result | 
            where status == "unspecified" | 
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

# Helper command to show only missing files
export def "main missing" [
    path: string
    --db-path: string = ""
] {
    main $path --db-path $db_path | 
    from json | 
    where status == "missing" | 
    get path
}

# Helper command to show only unspecified files
export def "main unspecified" [
    path: string
    --db-path: string = ""
] {
    main $path --db-path $db_path | 
    from json | 
    where status == "unspecified" | 
    get path
}