{
  description = "Local flake for testing path dependencies";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
  };

  outputs = { self, nixpkgs }:
    {
      lib.testFunction = x: x + 1;
    };
}