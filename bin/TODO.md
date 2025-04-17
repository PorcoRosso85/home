# TODO.md

## TODO管理 ✅

- web対応？spreadsheet？
- TODO同士の依存関係？編集先アドレス
  - プロジェクトやディレクトリもあくまでグルーピングでしかない
- taskwarriorの検討 https://taskwarrior.org/
- taskwarrior-webとtailscaleの検討 https://github.com/tmahmood/taskwarrior-web
  - TODOを抽出してタスクとして管理してほしい
- ✅TODOは作成しないようにする方向で <- json作成がTODOとなる
  - TODOの入れ替え修正に課題

## toolsのひとつ `another_aichat` toolを、単体で使用可能なMCPクライアントに昇華する

- MCP = model context protocol
- クライアント機能
  - toolsを呼び出せる
  - toolsとして自分自身を呼び出せる＋再帰的に他のツールを呼び出せる
  -  another_aichatを「自身を含めたtools呼び出しtool」として再帰可能にする
- 結果 `aichat xxxして`とリクエストするだけでタスク分割やファイル生成を可能にする

## toolsをデフォルト値設定済みsourceをしたかのように簡単に呼びたい

- argc completion?
- wrapper? sourceする用ファイルパスから、関数をビルドするイメージ `source.txt`
- bin内でsourceするしないを判断されたtools群
  - もしくはビルドされたらsourceしたとする
  - sourceする場合はファイル実行されないことを確認したい
  - sourceせずに便利な使い方が知りたい

## 以下のような管理も任せたい

- ただ作り散らかすクセはどうにかしないといけない
- いわゆる管理ができない
  - 大きさをとどめる
  - 規則に従って小さく拡張する
  - ヒトが追いつかない

## aichat, sourceするかフラグ足りないときコマンドexample出してしまってほしい

## toolsが増大したときのtools探索MCPもしくはhelp充実化

- RAGも検討, その場合aichatが使用可能

## ociでバケットを機能させたい
./oci.nuファイルのみで完結する

<!-- NOTE cloudflareならflarectl -->
<!-- NOTE もしかして実行スクリプト要らなかった？→どうせ正しいプロンプトするなら記録残しておいてもらおうと思っただけだったんだが -->
<!-- WARN スクリプトにしなくていい場合もあるね -->
<!-- NOTE それか最初に動作やってもらってhelpとか理解してもらって, できたらスクリプトに残してもいいかもね -->


## バケットとプロジェクトをsyncしたい
<!-- TODO ディレクトリすべてをsyncさせるのにs3cmd? https://github.com/s3fs-fuse/s3fs-fuse https://github.com/peak/s5cmd https://github.com/nidor1998/s3sync -->
<!-- TODO https://www.perplexity.ai/search/https-github-com-awslabs-mount-IoRR5XljT6qGZRjXBE7mAQ -->



##
after
ociでnixosデプロイしたい, 結果cronなどでシングルファイルをいつでも稼働できるようにしたい
<!-- https://mtlynch.io/notes/nix-oracle-cloud/?utm_source=perplexity -->
<!-- https://prithu.dev/notes/installing-nixos-on-oracle-cloud-arm-instance/ -->
他にも
- nixpkgsセルフホスト


## lean型が適切なプロンプトとして機能するか確認したい
after
要件 -> inductive/typedclass -> 実装


## lean, 対既存プロジェクト
after
各関数についてtypedclass生成, さらにそのためのinductiveを生成をするプロンプトがほしい
ループ処理したい
動作確認方法を確立したい「ｘｘｘできてたら期待通り型が生成できている」
before
?


## lean, 対全プロジェクト
before
above...
after
inductive, typedclassによる依存関係グラフを加工可能にしたい
UIでの表示もしたいし
LLMで指示可能にしたい


##
after
leanプロジェクトをgithubへ -> 各プロジェクトからleanをflakeとして
before
各プロジェクトからleanプロジェクトを symlink


## 
after
leanプロジェクトにファイル複数を配列で引数として渡したい
typedclassを扱えるようになりたい
before
?



## 格闘ゲームに関するアプリの市場調査


## tailscale ✅
after
ファイルのバックアップ
外部ユーザーにシングルファイルへの操作可能とする？


## format = predict(prompt(text), example)
## explaination = predict(prompt(text, format,), example)
## TODOはleanで書いたほうが楽か？ lean(todo) = predict(prompt(text), ) | lean
## 計画をleanなどのプロンプト言語で書き, コミットしたとき、AIがその差分を埋めるため/その差分でも埋められていない設計を埋めるため自律的に動く


## DB格納用 設計・バージョン管理スキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DesignVersion",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "description": "任意のバージョン識別子（例: 1.0.0、dev-20240401など）",
      "examples": ["1.0.0", "2.1.3-beta"]
    },
    "fileToUpdate": {
      "type": "array",
      "description": "変更のあった関数型スキーマJSONのURI配列",
      "items": {
        "type": "string",
        "format": "uri"
      }
    },
    "startDate": {
      "type": "string",
      "format": "date",
      "description": "このバージョンの対応作業 開始予定日"
    },
    "endDate": {
      "type": "string",
      "format": "date",
      "description": "このバージョンの対応作業 終了予定日"
    }
  },
  "required": ["fileToUpdate", "startDate", "endDate"]
}
```

---

- `version`は任意（バージョン識別子）
- `fileToUpdate`は変更のあった関数型スキーマURIリスト
- `startDate`・`endDate`は開始・終了予定日


