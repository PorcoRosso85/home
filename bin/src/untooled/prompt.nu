#!/usr/bin/env -S nix shell nixpkgs#nushell nixpkgs#lean4 --command nu

export def main [...args] {
  # TODO leanfile.lean設定できている -> elan/lakeがエントリポイントを知る -> ビルド可能 -> leanがそれを拝借できる
  # 1. 環境自体はこのshebangで用意するが、パス基準は先方へ or
  # 1. 参照先のleanもしくはlakeの環境を使用するようにしたい or
  # 1. もしくはこっちのleanを整える or
  #
  # TODO
  # 他からここを参照された時もそもそも相対パスで追いかけてくれない、、、このファイルを参照したときには一時このファイルを起点にしてくれないと
  # あるいは
  # nixpkgsをすべての絶対パスにする, nixあるところにパッケージあり, nixに問い合わせれば環境もスクリプトも使える
  #   "共通処理だからここ" "依存処理だからここ" という判定は大きなボトルネック
  #   パッケージをFZF探索できたらもっとうれしい
  # TODO
  # パッケージ公開＝ドキュメント可能＝zenn, qiita, note,,, nixでビルド＝公開する, cliやスクリプトファイルをnixで使いこなす
  # 
  # WARN いったん参照先をスクリプトぽく利用する
  # 
  (
    lean --run /home/nixos/lean/Src/Prompt.lean
  )
}

