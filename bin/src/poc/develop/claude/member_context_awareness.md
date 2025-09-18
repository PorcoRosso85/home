# Member の位置認識能力分析

## 現在のmember起動時の情報

```
[org system] ──起動──> [Claude member]
                            │
                            ├─ 環境変数
                            │   ├─ DB_URI
                            │   └─ （他には？）
                            │
                            ├─ 作業ディレクトリ
                            │   └─ /home/nixos/.worktrees/claude-org/auth-impl-123456/
                            │
                            └─ プロンプト
                                └─ "JWT認証実装"
```

## memberが「知っている」こと

### ✅ 確実に取得可能

1. **現在のディレクトリ**
   ```bash
   pwd
   # /home/nixos/.worktrees/claude-org/auth-impl-123456/
   ```

2. **sparse-checkoutの内容**
   ```bash
   git sparse-checkout list
   # src/auth
   ```

3. **作業対象ディレクトリ構造**
   ```bash
   ls -la
   # src/
   #   auth/
   #     （ここが作業場所）
   ```

### ❓ 不明確な情報

1. **自分のタスクID**
   ```
   auth-impl-123456 は取得可能？
   → worktreeパスから推測は可能
   ```

2. **プロジェクト全体での位置**
   ```
   「src/auth」が何のプロジェクトの一部？
   → sparse-checkoutで見えない
   ```

3. **他のmemberの存在**
   ```
   並行して動いている他タスク？
   → 知る術がない
   ```

## 位置情報の活用例

### GraphDBクエリでの文脈利用

```
[Claude member の思考]
    │
    ├─ 「私は src/auth/ で作業中」
    ├─ 「これは認証モジュール」
    └─ 「この文脈でのエラー解決策を検索」
        │
        └─ MATCH (s:Solution)
            WHERE s.context =~ '.*auth.*'
            OR s.module = 'authentication'
```

### 問題：プロジェクトタイプの推測

```
現状:
src/auth/ だけ見える
    │
    ├─ Rust project？
    ├─ Node.js project？
    └─ Python project？
        │
        └─ Cargo.toml が見えない（sparse-checkout外）
```

## 改善案：最小限の文脈情報追加

### 環境変数で提供

```bash
# org/main.sh.template で設定
export WORK_CONTEXT='{
  "project_type": "rust",
  "module": "auth",
  "task_id": "auth-impl-123456",
  "target_dir": "src/auth"
}'
```

### またはプロンプトに含める

```bash
launch_member --prompt "
作業情報:
- 場所: src/auth
- 言語: Rust
- タスク: JWT認証実装
"
```

## 現実的な評価

### memberの位置認識

```
ローカル情報:  ★★★★★ （完全に把握）
├─ pwd
├─ ls
└─ git status

プロジェクト文脈: ★★☆☆☆ （推測に依存）
├─ 言語（ファイル拡張子から）
├─ フレームワーク（不明）
└─ 全体構造（見えない）

グローバル文脈: ★☆☆☆☆ （ほぼ不明）
├─ 他タスクとの関係
├─ プロジェクト全体の目的
└─ 依存関係
```

## 結論

**memberは「自分の作業ディレクトリ」は完全に把握できるが、「プロジェクト全体での位置」は限定的**

これで十分か、追加情報が必要かは、タスクの複雑さ次第：
- 単純なモジュール実装: 現状で十分
- 統合的な機能開発: 追加文脈が必要