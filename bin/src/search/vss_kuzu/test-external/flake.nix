{
  description = "Test external usage of vss-kuzu";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    vss-kuzu.url = "path:..";  # 親ディレクトリのvss-kuzuを参照
  };

  outputs = { self, nixpkgs, flake-utils, vss-kuzu }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # vss-kuzuからパッケージを取得
        vssKuzuPackage = vss-kuzu.packages.${system}.vssKuzu;
        
        # Python環境を作成
        pythonEnv = pkgs.python312.withPackages (ps: [
          vssKuzuPackage
        ]);
      in {
        packages.default = pythonEnv;
        
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
          
          shellHook = ''
            echo "Testing external VSS-KuzuDB usage"
            echo "================================"
            echo ""
            echo "Try: python -c 'import vss_kuzu; import log_py'"
          '';
        };
        
        apps.test = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "test-vss" ''
            echo "Testing VSS-KuzuDB imports..."
            ${pythonEnv}/bin/python -c "
import vss_kuzu
import log_py
print('✓ vss_kuzu imported successfully')
print('✓ log_py imported successfully')
print(f'  vss_kuzu version: {vss_kuzu.__version__}')
print(f'  log_py available: {hasattr(log_py, \"log\")}')
"
          ''}/bin/test-vss";
        };
      });
}