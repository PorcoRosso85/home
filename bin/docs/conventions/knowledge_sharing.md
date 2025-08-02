# 知識共有の設計原則

> "エラーを責めるな、デザインを改善せよ" - Don Norman

このドキュメントは、Flakeやモジュールが「ツールの使い方」という責務を持つ場合の設計原則を定義する。

## 基本理念

知識共有は**静的な説明**ではなく、**動的な発見**を通じて行われるべきである。

### ❌ アンチパターン：静的な使い方の押し付け

```nix
# 悪い例：変更に脆弱で、継承先での理解が困難
apps.how-to-use = {
  program = pkgs.writeShellScript "how-to" ''
    echo "Step 1: Run pyright --strict"
    echo "Step 2: Fix all errors"
    echo "Step 3: Add type annotations"
  '';
};
```

問題点：
- ツールのバージョンアップで陳腐化する
- 継承先の文脈を考慮していない
- カスタマイズの余地がない

### ✅ 推奨パターン：発見可能な設計

```nix
# 良い例：自己記述的で拡張可能
lib.toolKnowledge = {
  # ツール自体から情報を取得
  capabilities = pkgs.runCommand "capabilities" {} ''
    ${pkgs.tool}/bin/tool --help > $out
  '';
  
  # 組み合わせ可能なパターン
  patterns = {
    basic = args: "${pkgs.tool}/bin/tool ${args.input}";
    advanced = args: "${pkgs.tool}/bin/tool --complex ${args.config}";
  };
  
  # 実行時の発見を促す
  explore = pkgs.writeShellScriptBin "explore-tool" ''
    echo "Discovering tool capabilities..."
    ${pkgs.tool}/bin/tool --version
    ${pkgs.tool}/bin/tool --help | head -20
  '';
};
```

## 設計原則

### 1. 発見可能性（Discoverability）

知識は隠されているのではなく、探索可能でなければならない。

```nix
# 実装例
packages.tool-with-knowledge = pkgs.symlinkJoin {
  name = "tool-with-knowledge";
  paths = [ pkgs.tool ];
  postBuild = ''
    mkdir -p $out/share/knowledge
    
    # 動的に生成される情報
    ${pkgs.tool}/bin/tool --help > $out/share/knowledge/help.txt
    ${pkgs.tool}/bin/tool --version > $out/share/knowledge/version.txt
    
    # 探索の起点
    cat > $out/share/knowledge/START_HERE.txt << EOF
    Knowledge base location: $out/share/knowledge/
    Examples: ${self}/examples/
    Interactive guide: nix run ${self}#guide
    EOF
  '';
};
```

### 2. 漸進的開示（Progressive Disclosure）

初心者を圧倒せず、必要に応じて詳細を開示する。

```nix
apps = {
  # レベル1：最も基本的な使い方
  start = basicUsage;
  
  # レベル2：一般的なパターン
  patterns = commonPatterns;
  
  # レベル3：高度な機能
  advanced = advancedFeatures;
  
  # 現在のレベルを確認
  check-progress = showCurrentLevel;
};
```

### 3. エラーは学習機会（Errors as Learning Opportunities）

```nix
# エラーメッセージは教育的であるべき
assert condition || throw ''
  
  🤔 ${説明文：何が起きているか}
  
  This is expected because:
    ${理由：なぜこれが必要か}
  
  To fix this:
    ${具体的なアクション}
    
  Learn more:
    ${参照先}
'';
```

### 4. 組み合わせ可能性（Composability）

知識を部品として提供し、継承先が自由に組み合わせられるようにする。

```nix
lib = {
  # 基本的なビルディングブロック
  parseOutput = output: ...;
  filterErrors = diagnostics: ...;
  formatResults = results: ...;
  
  # 継承先が組み合わせて使用
  # myAnalyzer = compose [ parseOutput filterErrors formatResults ];
};
```

### 5. 自己文書化（Self-Documentation）

コード自体が使い方を示す。

```nix
# ファイル名が用途を示す
examples/
├── 01-first-time-setup.nix      # 番号で順序を示唆
├── check-single-file.nix         # 名前が機能を説明
├── integrate-with-ci.nix         # 実用的なユースケース
└── troubleshoot-common-errors.nix # 問題解決
```

## 実装チェックリスト

Flakeが知識共有の責務を持つ場合、以下を確認すること：

- [ ] **変更耐性**：ツールのバージョンアップに対応できるか？
- [ ] **発見可能**：継承先が必要な情報を見つけられるか？
- [ ] **段階的学習**：初心者から上級者まで対応しているか？
- [ ] **エラーの質**：エラーメッセージは教育的か？
- [ ] **カスタマイズ性**：継承先が独自のニーズに合わせられるか？

## メタデータによる責務の表明

```nix
# flake.nix で責務を明示的に宣言
meta.responsibilities = {
  provides = {
    tools = ["pyright"];
    knowledge = ["basic-usage", "error-handling", "patterns"];
    level = "beginner-to-intermediate";
  };
  
  guarantees = {
    documentation = "Always up-to-date with tool version";
    examples = "All examples are tested";
    discoverability = "Knowledge accessible via multiple paths";
  };
};
```

## 継続的な改善

知識共有は一度きりの実装ではない。フィードバックループを確立すること：

1. **使用パターンの収集**：どの機能がよく使われているか
2. **エラーパターンの分析**：どこでユーザーがつまずくか
3. **知識の更新**：新しいパターンや解決策の追加
4. **陳腐化した知識の削除**：もはや関連性のない情報の除去

## 関連規約

- [error_handling.md](./error_handling.md) - エラーメッセージの設計
- [module_design.md](./module_design.md) - モジュールの責務分離
- [testing.md](./testing.md) - 知識の正確性を保証するテスト