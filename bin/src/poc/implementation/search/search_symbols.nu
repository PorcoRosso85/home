#!/usr/bin/env nu

# ctags wrapper - Nushell implementation
# Will replace the Python implementation

# Main function to search symbols using ctags
export def search_symbols [
    path: string              # Path to search (file or directory)
    --ext: string = ""        # File extension filter
] {
    # Check if path exists
    if not ($path | path exists) {
        return {
            error: "Path not found"
            metadata: {searched_files: 0, search_time_ms: 0.0}
        }
    }
    
    # Get files to process
    let files = if ($path | path type) == "file" {
        [$path]
    } else {
        # Directory - use glob
        if $ext != "" {
            glob $"($path)/**/*.($ext)"
        } else {
            # Get all files and let ctags decide what it can process
            glob $"($path)/**/*" | where { |f| 
                ($f | path type) == "file"
            }
        }
    }
    
    # If no files found, return empty success
    if ($files | is-empty) {
        return {
            symbols: []
            metadata: {
                searched_files: 0
                search_time_ms: 0.0
            }
        }
    }
    
    # Process files with ctags
    let start_time = (date now)
    
    let symbols = $files | each { |file|
        # Run ctags for each file
        let ctags_output = (
            ^ctags --output-format=json --fields=+n -f - $file 
            | complete
        )
        
        if $ctags_output.exit_code != 0 {
            return []
        }
        
        # Parse ctags JSON output
        $ctags_output.stdout 
        | lines 
        | where { |line| $line != "" }
        | each { |line|
            try {
                let tag = ($line | from json)
                
                # Map ctags 'kind' to our type
                let symbol_type = match $tag.kind? {
                    "class" => "class"
                    "function" => "function"
                    "member" | "method" => "method"
                    "variable" => "variable"
                    "constant" => "constant"
                    _ => "unknown"
                }
                
                # Return standardized format
                {
                    name: $tag.name
                    type: $symbol_type
                    path: $tag.path
                    line: ($tag.line? | default 0 | into int)
                    column: null
                    context: null
                }
            } catch {
                # Skip malformed lines
                null
            }
        }
        | compact  # Remove nulls
    }
    | flatten
    
    let end_time = (date now)
    let elapsed_ms = (($end_time - $start_time) | into int) / 1_000_000
    
    # Return SearchSuccessDict format (convention compliant)
    {
        symbols: $symbols
        metadata: {
            searched_files: ($files | length)
            search_time_ms: $elapsed_ms
        }
    }
}

# CLI entry point
def main [
    path: string              # Path to search
    --ext: string = ""        # File extension filter
] {
    search_symbols $path --ext $ext | to json | print
}