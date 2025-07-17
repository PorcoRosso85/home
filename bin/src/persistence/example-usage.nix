# 呼び出し側のflake.nixの例

{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # 直接パス指定
    persistence.url = "path:/home/nixos/bin/src/persistence";
  };

  outputs = { self, nixpkgs, persistence }: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          python312Packages.kuzu  # Nixのkuzuパッケージ
        ];
        
        # persistenceモジュールをPYTHONPATHに追加
        shellHook = ''
          ${persistence.lib.shellHook}
          # または直接指定
          # export PYTHONPATH="${persistence.lib.pythonPath}:$PYTHONPATH"
          
          echo "Python with persistence module ready"
          echo "Try: python -c 'from kuzu.core.database import create_database'"
        '';
      };
    };
}