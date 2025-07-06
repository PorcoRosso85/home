# AppArmor wrapper のテスト例

{
  inputs = {
    apparmor-wrapper.url = "path:.";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    
    # テスト対象のflake
    readability.url = "path:../readability";
    similarity.url = "path:../similarity";
  };

  outputs = { self, apparmor-wrapper, nixpkgs, readability, similarity, ... }:
    let
      # readabilityをAppArmorでラップ
      readabilityWrapped = apparmor-wrapper.lib.wrapFlakeWithAppArmor {
        flake = readability;
        profileName = "readability-sandbox";
        enforceMode = false;
      };
      
      # similarityをカスタムプロファイルでラップ
      similarityWrapped = apparmor-wrapper.lib.wrapFlakeWithAppArmor {
        flake = similarity;
        profileName = "similarity-restricted";
        profilePath = ./profiles/similarity.profile;
        enforceMode = false;
      };
    in
    {
      # ラップされたパッケージをエクスポート
      packages = readabilityWrapped.packages // similarityWrapped.packages;
      apps = readabilityWrapped.apps // similarityWrapped.apps;
      
      # オリジナルとラップ版を比較するためのアプリ
      apps.x86_64-linux.compare = {
        type = "app";
        program = toString (nixpkgs.legacyPackages.x86_64-linux.writeShellScript "compare" ''
          echo "=== Testing Original vs Wrapped Versions ==="
          echo ""
          
          echo "1. Original readability:"
          ${readability.apps.x86_64-linux.default.program} --help | head -n 3
          
          echo ""
          echo "2. Wrapped readability (with AppArmor):"
          ${readabilityWrapped.apps.x86_64-linux.default.program} --help | head -n 3
          
          echo ""
          echo "3. Check if aa-exec is available:"
          if command -v aa-exec >/dev/null 2>&1; then
            echo "✓ aa-exec is available"
            aa-status --help | head -n 1 || echo "  (aa-status not available)"
          else
            echo "✗ aa-exec is NOT available (AppArmor not active)"
          fi
        '');
      };
    };
}