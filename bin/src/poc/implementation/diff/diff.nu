#!/usr/bin/env nu

# Diff tool - Compare KuzuDB LocationURIs with filesystem
# Nushell implementation replacing diff.sh

def main [
    path: string  # Directory to compare against
] {
    # Read JSON input from stdin
    let db_entries = $in | from json
    
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
            ($f | path type) == "file" and 
            not ($f | path basename | str starts-with ".")
        } |
        each { |f| $f | path expand } |
        sort
    
    # Calculate differences
    let missing = $db_uris | 
        where { |uri| 
            not ($uri in $fs_files)
        } |
        each { |path| 
            {path: $path, status: "missing"}
        }
    
    let unspecified = $fs_files | 
        where { |file| 
            not ($file in $db_uris)
        } |
        each { |path| 
            {path: $path, status: "unspecified"}
        }
    
    # Combine and output as JSON
    let result = $missing | append $unspecified
    
    $result | to json
}