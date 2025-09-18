{ pkgs ? import <nixpkgs> {} }:

pkgs.stdenv.mkDerivation {
  name = "test-example";
  
  buildCommand = ''
    echo "Running test from different directory..."
    echo "Test passed!" > $out
  '';
}