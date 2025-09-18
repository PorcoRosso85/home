# Output Path Tree Viewer

schemeリポジトリ内のJavaScriptに対する要件定義ファイル（`.require.json`）から出力パスを抽出し、ディレクトリ構造を可視化するツールです。

## 機能

- `data/requirements/` 内の JSON ファイルからデータを読み取り
- `outputPath.default` 属性を利用してディレクトリ構造を生成
- 選択したファイルの詳細情報と内容を表示

## 必要条件

- [Deno](https://deno.land/) (1.0.0以上)

## 使い方

1. サーバーを起動する：

```bash
cd /home/nixos/scheme/src/interface
./api.ts
```

または

```bash
deno run --allow-net --allow-read /home/nixos/scheme/src/interface/api.ts
```

2. ブラウザで次のURLにアクセスする：

```
http://localhost:8000/
```

3. 左側のツリーからファイルを選択すると、右側に詳細情報が表示されます。

## カスタマイズ

### ポート番号を変更する

`api.js` を開き、`PORT` の値を変更してください：

```javascript
// サーバー設定
const PORT = 8000; // ここを変更
```
