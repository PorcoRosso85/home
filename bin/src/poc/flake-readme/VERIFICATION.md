# Step 1 検証結果: self.outPath Git フィルタリング効果

## 実証された動作

### 1. Git追跡前の動作
```bash
# test-fd-integration/ignored-dir は .gitignore で除外されているが
# Git未追跡のため、Nixが flake 評価を拒否
error: Path 'bin/src/poc/flake-readme/test-fd-integration' in the repository "/home/nixos" is not tracked by Git.
```

### 2. Git追跡後の動作  
```bash
# git add test-fd-integration/ 実行後
# flake check が成功 → ignored-dir がmissingから除外された
checking flake output 'checks'...
running 1 flake checks...
building... [成功]
```

## 重要な発見

### inputs.self.outPath の効果
- **範囲**: Gitで追跡されているファイル/ディレクトリのみ
- **仕組み**: Nix flake評価時にGit追跡状態を確認
- **効果**: .gitignore準拠のフィルタリングが自動適用

### フレーク外パスとの差分
- **inputs.self.outPath**: Git追跡ファイルのみ対象
- **直接パス指定**: Git状態を無視、全ファイル対象

## 仕様の明確化

**「.gitignore準拠」の正確な条件:**
1. root = inputs.self.outPath を使用
2. flake自体がGitで追跡されている
3. Nix評価時にGit状態を確認

**フレーク外パス使用時:**
- Git効果は適用されない
- Pure Nix探索(readDir + 独自ignore)で動作

## 結論

✅ **仮説検証完了**: self.outPath利用により、"結果として".gitignore相当の効果を得られる

⚠️ **重要な条件**: flakeがGit追跡されている場合のみ有効