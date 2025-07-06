#!/usr/bin/env bash
# AppArmor無効化機能のテスト

echo "=== Testing AppArmor Disable Features ==="
echo ""

# テストコマンド
AA="nix run /home/nixos/bin/src/poc/apparmor#aa --"

echo "1. フラグによる無効化テスト:"
echo "   Command: $AA -n -v nixpkgs#hello"
echo "   Expected: AppArmor disabled by user request"
echo ""

echo "2. 環境変数による無効化テスト:"  
echo "   Command: DISABLE_APPARMOR=1 $AA -v nixpkgs#hello"
echo "   Expected: AppArmor disabled by user request"
echo ""

echo "3. NO_APPARMOR環境変数テスト:"
echo "   Command: NO_APPARMOR=1 $AA nixpkgs#hello" 
echo "   Expected: Runs without AppArmor (no verbose by default)"
echo ""

echo "4. 通常実行（AppArmorあり）:"
echo "   Command: $AA -v nixpkgs#hello"
echo "   Expected: Applying AppArmor profile"
echo ""

echo "実際のテストを実行するには上記コマンドを手動で実行してください。"