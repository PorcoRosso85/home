# kuzu-migrate Design Philosophy

## 問題：過剰な「親切」の害

従来のCLIツールの問題：
- 長大な静的エラーメッセージ
- 更新されない「解決策」の提案
- ユーザーの文脈を無視した画一的な指示
- LSPのような動的解析ができない

## 解決：最小限の事実報告

### 1. エラーは事実のみ

❌ 悪い例：
```
ERROR: DDL directory not found: ./ddl

Please create the DDL directory first:
  mkdir -p ./ddl
  nix run .#init

Learn more: https://github.com/...
```

✅ 良い例：
```
❌ directory not found: ./ddl
```

### 2. 状態確認は独立したコマンド

```bash
$ nix run .#check

DDL check: ./ddl
  exists: no
  
Environment:
  pwd: /home/user/project
  nearby DDLs:
    ./database/ddl
    ../other-project/ddl
```

### 3. 単一責務の徹底

各コマンドは1つのことだけ：
- `init`: DDL構造を作る（それだけ）
- `apply`: マイグレーションを実行する（それだけ）
- `check`: 現在の状態を報告する（それだけ）

### 4. flakeによる構造の保証

エラーメッセージで説明するのではなく、flakeが正しい使い方を強制：

```nix
# ユーザーは間違った使い方ができない
apps = kuzu-migrate.lib.mkKuzuMigration { 
  ddlPath = "./ddl";  # flakeがパスを管理
};
```

## 実装指針

1. **エラーメッセージは1行以内**
2. **「どうすべきか」は書かない**
3. **現在の状態（事実）のみ報告**
4. **診断は別コマンドで提供**
5. **flakeで正しい使い方を強制**