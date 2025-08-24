{
  description = "Test flake to verify edgartools overlay works correctly";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    edgartools.url = "path:../";  # 親ディレクトリのedgartools flake
  };

  outputs = { self, nixpkgs, edgartools }:
    let
      system = "x86_64-linux";
      
      # overlayを適用したpkgs
      pkgs = import nixpkgs {
        inherit system;
        overlays = [ edgartools.overlays.${system}.default ];
      };
    in
    {
      # 各Pythonバージョンでedgartoolsが使えることを確認
      packages.${system} = {
        # Python 3.9環境
        test-py39 = pkgs.python39.withPackages (ps: [
          ps.edgartools
        ]);
        
        # Python 3.10環境
        test-py310 = pkgs.python310.withPackages (ps: [
          ps.edgartools
        ]);
        
        # Python 3.11環境
        test-py311 = pkgs.python311.withPackages (ps: [
          ps.edgartools
        ]);
        
        # Python 3.12環境
        test-py312 = pkgs.python312.withPackages (ps: [
          ps.edgartools
        ]);
        
        # 統合テストスクリプト
        test-all = pkgs.writeShellScriptBin "test-overlay" ''
          echo "Testing edgartools overlay with multiple Python versions..."
          echo ""
          
          echo "=== Python 3.9 ==="
          ${self.packages.${system}.test-py39}/bin/python -c "
          import sys
          import edgar
          print(f'Python {sys.version_info.major}.{sys.version_info.minor}: ✓ edgar module imported')
          "
          
          echo ""
          echo "=== Python 3.10 ==="
          ${self.packages.${system}.test-py310}/bin/python -c "
          import sys
          import edgar
          print(f'Python {sys.version_info.major}.{sys.version_info.minor}: ✓ edgar module imported')
          "
          
          echo ""
          echo "=== Python 3.11 ==="
          ${self.packages.${system}.test-py311}/bin/python -c "
          import sys
          import edgar
          print(f'Python {sys.version_info.major}.{sys.version_info.minor}: ✓ edgar module imported')
          "
          
          echo ""
          echo "=== Python 3.12 ==="
          ${self.packages.${system}.test-py312}/bin/python -c "
          import sys
          import edgar
          print(f'Python {sys.version_info.major}.{sys.version_info.minor}: ✓ edgar module imported')
          "
          
          echo ""
          echo "✅ All overlay tests passed!"
        '';
      };
      
      # 開発シェル（テスト実行用）
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          self.packages.${system}.test-all
        ];
        
        shellHook = ''
          echo "Overlay test environment ready"
          echo "Run: test-overlay"
        '';
      };
    };
}