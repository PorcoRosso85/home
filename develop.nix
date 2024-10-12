{ pkgs }:

pkgs.mkShell {
  buildInputs = [
  ];

  shellHook = ''
    echo "Hello Dev!!"
  '';

}
