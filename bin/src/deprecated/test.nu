#!/usr/bin/env -S nix shell nixpkgs#nushell --command nu

print "Test started..."

let max_retries = 0 # TODO
let retry_count = 0
print "retry_count"
print $retry_count

loop {
    try {
        let result = (./test.ts)
        print $result

        if $result =~ "ok" {
            print "テスト成功しました"
            break
        } else if $result =~ "error" or $result =~ "throw" {
            print "テスト失敗（エラー発生）"
        } else {
            print "テスト失敗（異常終了）"
        }
    } catch {
        print $"テスト失敗しました（エラー発生）。エラー: ($in)"
        let $retry_count = $retry_count + 1
        if $retry_count <= $max_retries {
            print $"リトライ回数: ($retry_count)"
            print "テスト失敗したので、コードを再生成します"
            # ここにコード再生成の処理を追加
        } else {
            print "最大リトライ回数に達しました。"
            break
        }
    }

    if $retry_count >= $max_retries {
        break # 最大リトライ回数に達したらループを抜ける
    }
}
