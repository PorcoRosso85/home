# エントリーポイント規約

## 責務分離

| レイヤー | ファイル | 責務 |
|:--|:--|:--|
| Flake | `flake.nix` | アプリ定義（default, test, readme） |
| CLI | `main.{ext}` | 引数解析、I/O制御、エラー表示 |
| Library | `mod.{ext}` | 公開API、型定義 |

## 実装パターン

### CLIエントリーポイント（main.{ext}）
```python
# 標準入力がある場合のみ処理、なければヘルプ表示
if sys.stdin.isatty():
    print_usage()
else:
    process_input()
```

### Flake連携
- `apps.default`: 利用可能コマンド一覧（BuildTime評価）
- `apps.test`: `nix run .#test`
- `apps.readme`: `cat ${./README.md}`

## 関連規約
- [nix_flake.md](./nix_flake.md) - Flakeレイヤーの詳細
- [module_design.md](./module_design.md) - ライブラリ設計