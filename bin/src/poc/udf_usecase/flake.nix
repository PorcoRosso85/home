{
  description = "KuzuDB UDF development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.mkShell {
      buildInputs = with nixpkgs.legacyPackages.x86_64-linux; [
        python311
        stdenv.cc.cc.lib
      ];
      
      shellHook = ''
        export LD_LIBRARY_PATH="${nixpkgs.legacyPackages.x86_64-linux.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
      '';
    };
  };
}