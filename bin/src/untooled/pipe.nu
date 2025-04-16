#!/usr/bin/env -S nix shell nixpkgs#nushell --command nu

def main [] {
    print open
    
    # Use a safer approach with select-timeout to avoid blocking
    try {
        # Try to read from stdin with a timeout
        let input = (^timeout 0.1 cat | default "")
        
        if ($input | is-empty) {
            print "No input provided via pipe."
        } else {
            $input | str upcase
        }
    } catch {
        print "No input provided via pipe."
    }
}
