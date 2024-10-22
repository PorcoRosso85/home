{
  description = "typescript";

  inputs = {
    # 下記は不要かもしれない, 呼び出し元のflakeから継承されるため
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          nodejs_22
          bun
          pnpm
        ];

        shellHook = ''
          echo "##### typescript by flake #####"
        '';
      };
    };
}
