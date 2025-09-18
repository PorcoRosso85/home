# AppArmor効果検証方法

## 1. プロセス状態の確認

### aa-status での確認
```bash
# AppArmorの状態確認
$ sudo aa-status | grep -A5 "restricted"

# 特定プロセスの確認
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- -v nixpkgs#hello &
$ PID=$!
$ sudo cat /proc/$PID/attr/current
# 出力例: restricted (enforce) または restricted (complain)
```

### procファイルシステムで直接確認
```bash
# テストスクリプト作成
$ cat > test-apparmor.sh << 'EOF'
#!/usr/bin/env bash
echo "PID: $$"
echo "AppArmor profile: $(cat /proc/$$/attr/current 2>/dev/null || echo 'unconfined')"
sleep 10
EOF

$ chmod +x test-apparmor.sh

# 通常実行
$ ./test-apparmor.sh
# 出力: unconfined

# AppArmor適用
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- ./test-apparmor.sh
# 出力: restricted (enforce)
```

## 2. 実際の制限テスト

### ネットワークアクセステスト
```nix
# test-network.nix
{
  description = "Network access test";
  
  outputs = { self, nixpkgs }: {
    packages.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.writeShellScriptBin "test-network" ''
      echo "Testing network access..."
      ${nixpkgs.legacyPackages.x86_64-linux.curl}/bin/curl -s https://example.com > /dev/null && echo "✓ Network OK" || echo "✗ Network blocked"
    '';
  };
}
```

```bash
# strictプロファイルでネットワークブロック確認
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- -p strict ./test-network.nix
# 出力: ✗ Network blocked
```

### ファイルアクセステスト
```nix
# test-file-access.nix
{
  description = "File access test";
  
  outputs = { self, nixpkgs }: {
    packages.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.writeShellScriptBin "test-files" ''
      echo "=== File Access Test ==="
      
      # /tmp書き込み
      echo "test" > /tmp/aa-test 2>/dev/null && echo "✓ /tmp write OK" || echo "✗ /tmp write blocked"
      
      # ホーム読み取り  
      ls ~ > /dev/null 2>&1 && echo "✓ Home read OK" || echo "✗ Home read blocked"
      
      # SSH鍵読み取り
      cat ~/.ssh/id_rsa 2>/dev/null && echo "✗ SSH key readable!" || echo "✓ SSH key protected"
      
      # /etc書き込み
      touch /etc/test 2>/dev/null && echo "✗ /etc writable!" || echo "✓ /etc protected"
    '';
  };
}
```

## 3. audit.d ログ確認

```bash
# auditdが有効な場合
$ sudo journalctl -u audit | grep -i apparmor

# またはdmesgで確認
$ sudo dmesg | grep -i apparmor

# リアルタイムモニタリング
$ sudo journalctl -f | grep -i denied
```

## 4. 統合テストスクリプト

```nix
# apparmor-test.nix
{
  description = "AppArmor verification test suite";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    apparmor.url = "path:/home/nixos/bin/src/poc/apparmor";
  };
  
  outputs = { self, nixpkgs, apparmor }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in
    {
      packages.x86_64-linux.test = pkgs.writeShellScriptBin "aa-test" ''
        set -e
        
        echo "=== AppArmor Verification Test ==="
        echo ""
        
        # 1. プロファイル確認
        echo "1. Checking current profile:"
        profile=$(cat /proc/$$/attr/current 2>/dev/null || echo "unconfined")
        echo "   Current: $profile"
        
        if [[ "$profile" == "unconfined" ]]; then
          echo "   ⚠️  Not running under AppArmor"
        else
          echo "   ✓ Running under AppArmor profile: $profile"
        fi
        
        echo ""
        echo "2. Testing restrictions:"
        
        # ネットワーク
        ${pkgs.curl}/bin/curl -s --max-time 2 https://example.com > /dev/null 2>&1 && \
          echo "   ✓ Network: allowed" || echo "   ✗ Network: blocked"
        
        # ファイルアクセス
        echo "test" > /tmp/aa-test-$$ 2>/dev/null && \
          echo "   ✓ /tmp write: allowed" || echo "   ✗ /tmp write: blocked"
        
        cat ~/.ssh/id_rsa 2>/dev/null && \
          echo "   ✗ SSH keys: ACCESSIBLE (BAD!)" || echo "   ✓ SSH keys: protected"
        
        touch /etc/aa-test 2>/dev/null && \
          echo "   ✗ /etc write: ALLOWED (BAD!)" || echo "   ✓ /etc write: blocked"
        
        echo ""
        echo "3. Profile details:"
        if command -v aa-status >/dev/null 2>&1; then
          sudo aa-status 2>/dev/null | grep -A2 "$profile" || echo "   (requires sudo)"
        else
          echo "   aa-status not available"
        fi
      '';
      
      apps.x86_64-linux.verify = {
        type = "app";
        program = toString (pkgs.writeShellScript "verify-aa" ''
          echo "Testing without AppArmor:"
          ${self.packages.x86_64-linux.test}/bin/aa-test
          
          echo ""
          echo "Testing with AppArmor (restricted):"
          ${apparmor.apps.x86_64-linux.aa.program} ${self.packages.x86_64-linux.test} 
          
          echo ""
          echo "Testing with AppArmor (strict):"
          ${apparmor.apps.x86_64-linux.aa.program} -p strict ${self.packages.x86_64-linux.test}
        '');
      };
    };
}
```

## 5. complainモードでの検証

```bash
# complainモードで実行して違反を記録
$ nix run /home/nixos/bin/src/poc/apparmor#aa -- -c ./my-app

# ログ確認
$ sudo journalctl -g apparmor | grep -i "audit.*allowed"
```

## 推奨テスト手順

1. **基本確認**: `/proc/PID/attr/current` でプロファイル適用確認
2. **制限確認**: ファイル/ネットワークアクセステスト
3. **ログ確認**: audit.d/journalctlで拒否ログ確認
4. **complainモード**: 本番前に違反箇所を確認

これらの方法でAppArmorが実際に効いているか確認できます。