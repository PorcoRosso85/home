#!/usr/bin/env nu

# 最も汎用的なバージョン - パラメータで動作を完全制御
# 使用例: nu universal.nu run ./app --threshold 100
#        nu universal.nu test github:owner/repo
#        cat data.csv | nu universal.nu pipe ./app --format json

def main [
    action: string    # run, test, readme, pipe, check
    target: string    # ディレクトリ、URI、flake参照
    ...args          # 追加の引数
] {
    match $action {
        "readme" | "r" => {
            nix run $target -- --readme
        }
        "test" | "t" => {
            nix run $target -- --test
        }
        "run" => {
            nix run $target -- ...$args
        }
        "pipe" | "p" => {
            # 標準入力を期待
            $in | nix run $target -- ...$args
        }
        "check" | "c" => {
            # サポートしているプロトコルをチェック
            let protocols = ["readme", "test", "help", "version"]
            print $"Checking ($target)..."
            
            $protocols | each {|proto|
                let result = try {
                    nix run $target -- $"--($proto)" err> /dev/null out> /dev/null
                    $"✓ --($proto)"
                } catch {
                    $"✗ --($proto)"
                }
                print $result
            }
        }
        "usage" | "u" => {
            # 使用例だけを抽出
            nix run $target -- --readme 
            | lines 
            | skip until {|l| $l =~ "Usage|Example"} 
            | take until {|l| $l starts-with "#"}
        }
        _ => {
            print $"Unknown action: ($action)"
            print "Available: run, test, readme (r), pipe (p), check (c), usage (u)"
        }
    }
}