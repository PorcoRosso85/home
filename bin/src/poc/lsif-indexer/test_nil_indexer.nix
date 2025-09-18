{ pkgs ? import <nixpkgs> {} }:

let
  myFunction = x: x * 2;
  myVariable = 42;
in
{
  hello = pkgs.hello;
  result = myFunction myVariable;
  
  nested = {
    foo = "bar";
    baz = 123;
  };
}