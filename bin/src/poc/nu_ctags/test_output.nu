#!/usr/bin/env nu

source symbols.nu

# kuzu_query_loggerのシンボルを取得して表示
let results = symbols ./kuzu_query_logger/ --ext py

print "=== シンボル数 ==="
print $"Total symbols: ($results | length)"

print "\n=== シンボルタイプ別統計 ==="
$results | group-by type | transpose key value | each { |r| {type: $r.key, count: ($r.value | length)} } | print

print "\n=== 最初の10件 ==="
$results | select name type line | first 10 | print

print "\n=== JSON形式で最初の5件 ==="
$results | first 5 | to json | print