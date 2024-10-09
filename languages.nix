{ pkgs, ... }:

with pkgs; [
  nodePackages.pnpm
  biome
  typescript-language-server

  pulumi
]
