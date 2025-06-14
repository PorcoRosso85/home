#!/usr/bin/env -S nix shell nixpkgs#uv nixpkgs#nushell --command nu

# このファイルは
# ファイル配列を受け取り
# ファイルを実行し
# その結果をexit codeとしてkvでjson返却する
# {
#   "file": "./xxx.nu",
#   "code": 0 # or over 1 for errors
# }
export def main [
    file: string  # 実行するファイルパスのリスト
] {
    # ファイルが存在するか確認
    if not ($file | path exists) {
        return {
            file: $file,
            code: 127,
            error: "File not found"
        }
    }

    # ファイルを実行
    let result = do -i { nu $file }
    print "result" $result

    # 終了コードを取得
    let exit_code = if ($result.exit_code == null) {
        0
    } else {
        $result.exit_code
    }

    # 結果をJSON形式で返す
    {
        file: $file,
        code: $exit_code
    }
}
