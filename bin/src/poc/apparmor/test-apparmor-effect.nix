{
  description = "Test to verify AppArmor is actually working";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        packages.default = pkgs.writeShellScriptBin "test-apparmor" ''
          #!/usr/bin/env bash
          set -euo pipefail
          
          echo "=== AppArmor Effect Test ==="
          echo ""
          echo "PID: $$"
          echo ""
          
          # 1. 現在のAppArmorプロファイル確認
          echo "1. Current AppArmor profile:"
          profile=$(cat /proc/$$/attr/current 2>/dev/null || echo "unconfined")
          echo "   → $profile"
          
          if [[ "$profile" != "unconfined" ]]; then
            echo "   ✓ Running under AppArmor!"
          else
            echo "   ⚠️  Not protected by AppArmor"
          fi
          
          echo ""
          echo "2. Testing file access restrictions:"
          
          # /tmp書き込みテスト（通常は許可）
          if echo "test" > /tmp/aa-test-$$ 2>/dev/null; then
            echo "   ✓ /tmp write: allowed"
            rm -f /tmp/aa-test-$$
          else
            echo "   ✗ /tmp write: BLOCKED"
          fi
          
          # ホームディレクトリ読み取り（プロファイルによる）
          if ls ~ >/dev/null 2>&1; then
            echo "   ✓ Home read: allowed"
          else
            echo "   ✗ Home read: BLOCKED"
          fi
          
          # SSH鍵アクセステスト（通常は拒否すべき）
          if [[ -f ~/.ssh/id_rsa ]]; then
            if cat ~/.ssh/id_rsa >/dev/null 2>&1; then
              echo "   ⚠️  SSH key: READABLE (security risk!)"
            else
              echo "   ✓ SSH key: protected"
            fi
          else
            echo "   - SSH key: not found (test skipped)"
          fi
          
          # /etc書き込みテスト（通常は拒否すべき）
          if touch /etc/aa-test-$$ 2>/dev/null; then
            echo "   ⚠️  /etc write: ALLOWED (security risk!)"
            rm -f /etc/aa-test-$$
          else
            echo "   ✓ /etc write: blocked"
          fi
          
          echo ""
          echo "3. Testing network access:"
          
          # ネットワークアクセステスト
          if ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com >/dev/null 2>&1; then
            echo "   ✓ Network: allowed"
          else
            echo "   ✗ Network: BLOCKED"
          fi
          
          echo ""
          echo "4. Process information:"
          echo "   Command: $(cat /proc/$$/comm 2>/dev/null || echo 'unknown')"
          echo "   Executable: $(readlink /proc/$$/exe 2>/dev/null || echo 'unknown')"
          
          # デバッグ用：利用可能な場合のみ
          if command -v aa-enabled >/dev/null 2>&1; then
            echo ""
            echo "5. AppArmor system status:"
            aa-enabled && echo "   ✓ AppArmor is enabled" || echo "   ✗ AppArmor is disabled"
          fi
        '';
        
        # 違反を意図的に起こすテスト
        packages.violate = pkgs.writeShellScriptBin "test-violations" ''
          echo "=== Intentional AppArmor Violations Test ==="
          echo "(This should fail under strict profile)"
          echo ""
          
          # 禁止されるべき操作を試行
          operations=(
            "cat /etc/passwd"
            "cat ~/.ssh/id_rsa" 
            "touch /etc/test-file"
            "mkdir /root/test"
            "${pkgs.curl}/bin/curl https://example.com"
          )
          
          for op in "''${operations[@]}"; do
            echo -n "Testing: $op ... "
            if $op >/dev/null 2>&1; then
              echo "ALLOWED ⚠️"
            else
              echo "BLOCKED ✓"
            fi
          done
        '';
        
        # 比較テスト実行スクリプト
        apps.compare = {
          type = "app";
          program = toString (pkgs.writeShellScript "compare-apparmor" ''
            echo "=== Comparing with and without AppArmor ==="
            echo ""
            echo "1. Running WITHOUT AppArmor:"
            echo "----------------------------"
            ${self.packages.${system}.default}/bin/test-apparmor
            
            echo ""
            echo ""
            echo "2. Running WITH AppArmor (restricted profile):"
            echo "----------------------------------------------"
            echo "(Execute with: nix run /home/nixos/bin/src/poc/apparmor#aa -- ${self})"
            echo ""
            echo "3. Running WITH AppArmor (strict profile):"
            echo "------------------------------------------"
            echo "(Execute with: nix run /home/nixos/bin/src/poc/apparmor#aa -- -p strict ${self})"
          '');
        };
      });
}