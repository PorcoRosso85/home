#!/usr/bin/awk -f
# Kuzu累積クエリ結果を処理して、各ファイルの最終状態を判定

BEGIN {
    count = 0
    prev_file = ""
}

# ファイルパスを含む行を処理
/│.*file:/ || /│.*http:/ || /│.*https:/ {
    # フィールドを抽出（│で区切られている）
    split($0, fields, "│")
    
    # 空白を削除
    gsub(/^[ \t]+|[ \t]+$/, "", fields[2])
    gsub(/^[ \t]+|[ \t]+$/, "", fields[4])
    
    file = fields[2]
    change_type = fields[4]
    
    # 新しいファイルの場合
    if (file != prev_file && file != "") {
        # 最初の（最新の）レコードのみを考慮
        if (change_type != "DELETE") {
            count++
        }
        prev_file = file
    }
}

END {
    print count
}