# ./sl/pkgs.nix
{ stdenv
, lib
, ncurses # dependency
, makeWrapper # make is usually included in stdenv, but just to be sure
, src
}:

stdenv.mkDerivation {
  pname = "sl";
  version = src.rev or "git"; # Use the input revision

  inherit src;

  buildInputs = [ ncurses ];
  nativeBuildInputs = [ makeWrapper ]; # make is usually included in stdenv

  # sl's Makefile doesn't have an install target, so copy manually
  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin
    cp sl $out/bin/
    # Copy man page if it exists (sl probably doesn't have one)
    # mkdir -p $out/share/man/man1
    # cp sl.1 $out/share/man/man1/
    runHook postInstall
  '';

  meta = with lib; {
    description = "Steam Locomotive runs across your terminal";
    homepage = "https://github.com/mtoyoda/sl";
    license = licenses.publicDomain; # or if unknown, use unfree/free
    platforms = platforms.unix; # uses curses, so Unix-like systems
  };
}
