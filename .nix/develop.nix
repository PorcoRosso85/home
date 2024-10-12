{ pkgs }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # nix
    # installed

    # markdown
    marksman
  ]
  ++ (import ./npm.nix { inherit pkgs; })
  ++ (import ./go.nix { inherit pkgs; })
  ++ (import ./python.nix { inherit pkgs; })
  ;

  shellHook = ''
    echo "Hello Dev!!"
  '';

}
