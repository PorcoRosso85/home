# Example AppArmor profile for wrapped applications

# ネットワークアクセス
network inet stream,
network inet dgram,

# ファイルシステムアクセス
/tmp/** rw,
/var/tmp/** rw,
@{HOME}/.cache/** rw,
@{HOME}/.config/** r,

# プロセス実行
/usr/bin/env ix,
/bin/sh ix,
/bin/bash ix,

# 標準的なライブラリ
/lib/** r,
/usr/lib/** r,
/nix/store/** r,

# デバイスアクセス
/dev/null rw,
/dev/zero rw,
/dev/random r,
/dev/urandom r,
/dev/tty rw,

# procファイルシステム
/proc/self/** r,
/proc/meminfo r,
/proc/cpuinfo r,

# 拒否ルール
deny @{HOME}/.ssh/** rw,
deny /etc/passwd w,
deny /etc/shadow rw,