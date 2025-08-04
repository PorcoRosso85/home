{
  description = "Modular scripts for Claude launcher";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system} = {
      # Project selector script
      select-project = pkgs.writeShellApplication {
        name = "select-project";
        runtimeInputs = with pkgs; [
          findutils
          coreutils
          gnugrep
          bash
          fzf
        ];
        text = builtins.replaceStrings 
          ["#!/usr/bin/env bash"] 
          [""] 
          (builtins.readFile ./select-project);
      };
      
      # Claude launcher script
      launch-claude = pkgs.writeShellApplication {
        name = "launch-claude";
        runtimeInputs = with pkgs; [
          coreutils
          bash
        ];
        text = builtins.replaceStrings 
          ["#!/usr/bin/env bash"] 
          [""] 
          (builtins.readFile ./launch-claude);
      };
      
      # Default package
      default = self.packages.${system}.select-project;
    };
  };
}