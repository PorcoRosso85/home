# entry
/entry

# 説明
LLM-firstなエントリポイントとして、自然言語でシステムと対話し、適切な実行パスを選択する。
従来のCLIオプション引数を廃止し、JSONデータオブジェクトまたはスクリプトファイルを入力として受け付ける。

# 実行内容
1. `nix run /full/path/to/flake` でシステムを起動
2. デフォルト（引数なし）の場合、READMEを表示してインタラクティブモードへ
3. `#run` サブコマンドで実行（JSONまたはスクリプトファイルを入力）
4. `#test` サブコマンドでテスト実行（テストシナリオファイルを入力）
5. 自然言語による問い合わせを解釈し、適切なテンプレートを生成

# 使用例

## requirement/graphの例

### デフォルト（README表示）
```bash
nix run /home/nixos/bin/src/requirement/graph
# → READMEを表示し、対話モードへ
```

### 実行例（JSONデータオブジェクト）
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

### 実行例（スクリプトファイル）
```bash
# create_requirements.json
cat > create_requirements.json << 'EOF'
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

nix run /home/nixos/bin/src/requirement/graph#run < create_requirements.json
```

### テスト例
```bash
# test_scenario.json
cat > test_scenario.json << 'EOF'
{
  "scenarios": [
    {
      "name": "要件作成と重複検出",
      "steps": [
        {"action": "create", "data": {"id": "req_001", "title": "ログイン機能"}},
        {"action": "create", "data": {"id": "req_002", "title": "ログイン機能"}},
        {"action": "assert", "condition": "duplicate_detected"}
      ]
    }
  ]
}
EOF

nix run /home/nixos/bin/src/requirement/graph#test < test_scenario.json
```

## poc/storage/r2の例

### デフォルト
```bash
nix run /home/nixos/bin/src/poc/storage/r2
# → R2操作ガイドを表示
```

### 実行例（バケット操作）
```bash
echo '{
  "operation": "create_bucket",
  "bucket_name": "my-data-bucket",
  "region": "auto"
}' | nix run /home/nixos/bin/src/poc/storage/r2#run

# または複数操作のスクリプト
cat > r2_operations.json << 'EOF'
[
  {"operation": "create_bucket", "bucket_name": "test-bucket"},
  {"operation": "upload", "bucket": "test-bucket", "key": "data.json", "content": "{}"},
  {"operation": "list_objects", "bucket": "test-bucket"}
]
EOF

nix run /home/nixos/bin/src/poc/storage/r2#run < r2_operations.json
```

# 設計原則

## 背景：LLMの動的生成能力の活用
LLMは以下を動的に生成可能である：
- 複雑なシェルスクリプト
- 構造化されたJSONデータオブジェクト
- テストシナリオ
- 実行計画

この能力を最大限活用するため、従来の固定的なCLIオプションを廃止し、
LLMが状況に応じて最適な入力形式を生成できる設計とする。

## 1. LLM-first
- 自然言語での問い合わせを優先
- 構造化データ（JSON）は二次的
- エラーメッセージも自然言語で

## 2. オプション引数の廃止
```bash
# ❌ 従来のCLI（禁止）
my-cli --create --id req_001 --title "認証機能"

# ✅ 新しい方式（推奨）
echo '{"template": "create_requirement", "parameters": {"id": "req_001", "title": "認証機能"}}' | nix run ...#run
```

## 3. 対話的インターフェース
```
$ nix run /home/nixos/bin/src/requirement/graph
> 新しい要件を作成したい
→ どのような要件ですか？タイトルと説明を教えてください。
> ユーザー認証機能。メールアドレスとパスワードでログインできるようにする。
→ 以下の内容で作成します：
  {
    "template": "create_requirement",
    "parameters": {
      "title": "ユーザー認証機能",
      "description": "メールアドレスとパスワードでログインできるようにする"
    }
  }
  実行しますか？ (y/n)
```

# 実装例（flake.nix）

```nix
{
  apps = {
    default = {
      type = "app";
      program = "${self.packages.${system}.entry}/bin/entry-readme";
    };
    
    run = {
      type = "app";
      program = "${self.packages.${system}.entry}/bin/entry-run";
    };
    
    test = {
      type = "app";
      program = "${self.packages.${system}.entry}/bin/entry-test";
    };
  };
  
  packages.entry = pkgs.writeScriptBin "entry" ''
    #!/usr/bin/env python3
    import json
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # JSONまたはスクリプトファイルを処理
        data = json.load(sys.stdin)
        process_operations(data)
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # テストシナリオを実行
        scenarios = json.load(sys.stdin)
        run_test_scenarios(scenarios)
    else:
        # READMEを表示して対話モード
        show_readme()
        interactive_mode()
  '';
}
```

# 関連ファイル
- ~/.claude/scripts/entry_process_template.py
- ~/.claude/scripts/entry_interactive.py