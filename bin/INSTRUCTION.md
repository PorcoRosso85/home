#

##

### permission
あなたはファイルに実行許可を与えることができないので
必要な場合はユーザーに以下を提出すること
- 実行許可をあたえるファイル
- そのcommand

### shebang
各拡張子でshebangのテンプレートが存在する
これはそのファイルを実行するための実行環境を含むものである

```py
#!/usr/bin/env -S nix shell nixpkgs#python312Packages.pytest_7 --command pytest -sv
```

### file name
ファイル名は`test*`, `*test`を付加しない
なぜなら各テストはファイル単位で行うためである

### test
testコードはユーザーの許可がない限り変更ができない
testコードを変更するべきと判断したときは、ユーザーにその理由の説明を行い許可を得ること
