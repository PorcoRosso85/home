# ./sl/parts.nix
{ inputs, lib, pkgs, system, config, self, ... }:

let
  # Define sl source from inputs
  sl-src = inputs.sl-src;
in
{
  # Package definition
  packages.sl = pkgs.callPackage ./pkgs.nix {
    src = sl-src;
    # ncurses and makeWrapper will be automatically resolved from pkgs
  };

  # Development shell definition
  devShells.sl = pkgs.mkShell {
    inputsFrom = [ config.packages.sl ]; # could also use self.packages.sl
    packages = with pkgs; [
      # Tools that might be useful during development
      gdb
    ];
  };
}