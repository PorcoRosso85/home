#!/usr/bin/env nu

# Diff tool - Compare KuzuDB LocationURIs with filesystem
# Nushell implementation replacing diff.sh

def main [
    path: string  # Directory to compare against
] {
    # Read JSON input from stdin
    let stdin_input = $in
    let db_entries = if ($stdin_input | is-empty) {
        []
    } else {
        $stdin_input | from json
    }
    
    # Extract and normalize URIs
    let db_uris = $db_entries | 
        get uri | 
        each { |uri|
            $uri | 
            str replace "file://" "" |
            str replace --regex "#.*" ""  # Remove fragments (e.g., #L42, #function_name)
        } |
        uniq |
        sort
    
    # Get all files from filesystem (excluding hidden files)
    let fs_files = glob $"($path)/**/*" | 
        where { |f| 
            ($f | path type) == "file"
        } |
        where { |f|
            not ($f | path basename | str starts-with ".")
        } |
        each { |f| $f | path expand } |
        sort
    
    # Create normalized results
    # All unique paths from both sources
    let all_paths = ($db_uris | append $fs_files) | uniq | sort
    
    # Create result with boolean flags
    let result = $all_paths | each { |path|
        {
            path: $path
            requirement_exists: ($path in $db_uris)
            implementation_exists: ($path in $fs_files)
        }
    } | where { |item|
        # Only include paths where there's a mismatch
        $item.requirement_exists != $item.implementation_exists
    }
    
    $result | to json
}