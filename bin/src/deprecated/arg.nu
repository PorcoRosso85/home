#!/usr/bin/env -S nix shell nixpkgs#nushell --command nu run

def main [arg] {
    # print "hello"
    # print $arg
    echo $"hello ($arg)"
}
