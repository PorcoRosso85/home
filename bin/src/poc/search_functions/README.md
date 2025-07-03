# search_functions

ctagsのJSON出力から関数・クラスを含むディレクトリパスを抽出

## 責務
**ctagsのコード解析結果 → ユニークなディレクトリパスのリスト**

## 使用例
```bash
universal-ctags -R --output-format=json . | nix develop -c search_functions
```

## 入力
```json
{"name":"main","path":"src/main.py","kind":"function","line":10}
{"name":"Config","path":"src/config.py","kind":"class","line":5}
```

## 出力
```
src
```