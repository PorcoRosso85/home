{
  description = "Email Core - ۅ���ƣ����MVP";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # �ñ��ա��ȋzpackages.defaultn��
        packages.default = pkgs.buildEnv {
          name = "email-core";
          paths = with pkgs; [
            bun
            typescript
            nodePackages.typescript-language-server
          ];
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            bun
            typescript
            nodePackages.typescript-language-server
          ];
        };
        # devShello�k��WjDŁkj�~g\�jD	
      });
}