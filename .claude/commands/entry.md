# entry
/entry

# 説明
既存のエントリポイントを構造化し、自己説明的なインターフェースを提供する。
オプション引数を廃止し、JSONベースの宣言的な操作方式に統一する。

# 実装内容
既存のflake.nixのエントリポイントを以下のように構造化：

1. **デフォルトアプリ（引数なし）**
   - プロジェクトの機能と使用方法を表示（自己説明）
   - 利用可能な操作の例を提示
   - 対話的ヘルプの提供

2. **`#run` サブコマンド**
   - JSON形式の操作を標準入力から受け付け
   - 単一操作またはバッチ処理（配列）に対応

3. **`#test` サブコマンド**
   - プロジェクトのテストスイートを実行
   - 詳細は `/bin/docs/conventions/test_infrastructure.md` に準拠

# 使用例

## requirement/graphの例

### デフォルト（自己説明）
```bash
nix run /home/nixos/bin/src/requirement/graph
# → プロジェクトの機能説明と操作例を表示
```

### 実行例（JSON操作）
```bash
echo '{
  "type": "template",
  "template": "create_requirement",
  "parameters": {
    "id": "req_001",
    "title": "ユーザー認証機能",
    "description": "システムへのログイン機能を実装する"
  }
}' | nix run /home/nixos/bin/src/requirement/graph#run
```

### バッチ実行例
```bash
cat > requirements.json << 'EOF'
[
  {
    "type": "template",
    "template": "create_requirement",
    "parameters": {"id": "req_001", "title": "認証機能"}
  },
  {
    "type": "template",
    "template": "create_requirement",
    "parameters": {"id": "req_002", "title": "認可機能"}
  }
]
EOF

nix run /home/nixos/bin/src/requirement/graph#run < requirements.json
```

## poc/storage/r2の例

### デフォルト（自己説明）
```bash
nix run /home/nixos/bin/src/poc/storage/r2
# → R2ストレージ操作の説明と使用例を表示
```

### 操作例
```bash
echo '{
  "operation": "create_bucket",
  "bucket_name": "my-data-bucket",
  "region": "auto"
}' | nix run /home/nixos/bin/src/poc/storage/r2#run
```

# 設計原則

## 1. 自己説明的インターフェース
- デフォルト実行時は必ず機能説明を表示
- 具体的な使用例を含める
- エラー時も次のアクションを示唆

## 2. 宣言的な操作
```bash
# ❌ 従来の命令的CLI
my-cli --create --id req_001 --title "認証機能"

# ✅ 宣言的なJSON操作
echo '{"template": "create_requirement", "parameters": {"id": "req_001", "title": "認証機能"}}' | nix run ...#run
```

## 3. 統一されたインターフェース
- すべての操作をJSON形式で統一
- 人間は例を見て理解し使用
- プログラム（LLMを含む）は構造化されたデータとして処理

# 実装パターン（flake.nix）

```nix
{
  apps = {
    default = {
      type = "app";
      program = "${pkgs.writeShellScript "show-help" ''
        cat << 'EOF'
        ====================================
        プロジェクト名: XXXシステム
        ====================================
        
        このシステムは...を提供します。
        
        使用方法:
        1. 操作を確認: nix run .
        2. 操作を実行: echo '<json>' | nix run .#run
        3. テスト実行: nix run .#test
        
        操作例:
        echo '{"operation": "example", "param": "value"}' | nix run .#run
        
        詳細はREADME.mdを参照してください。
        EOF
      ''}";
    };
    
    run = {
      type = "app";
      program = "${self.packages.${system}.runner}/bin/run";
    };
    
    test = {
      type = "app";
      program = "${self.packages.${system}.tester}/bin/test";
    };
  };
}
```

# 移行戦略
1. 既存のCLIインターフェースがある場合は、まずJSON操作を並列で追加
2. 使用例とドキュメントを充実させる
3. 十分な移行期間の後、旧インターフェースを削除

# 関連ファイル
- 各プロジェクトのREADME.md（詳細な使用方法）
- /bin/docs/conventions/nix_flake.md（flake規約）