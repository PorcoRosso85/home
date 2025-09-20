#!/usr/bin/env bash
set -Eeuo pipefail

root_dir=$(cd "$(dirname "$0")/.." && pwd)
hook="$root_dir/hooks/pre-receive"

echo "[TEST] pre-receive exists and is executable" >&2
[[ -f "$hook" ]] || { echo "missing: hooks/pre-receive" >&2; exit 1; }
[[ -x "$hook" ]] || { echo "not executable: hooks/pre-receive" >&2; exit 1; }

echo "[TEST] pre-receive accepts stdin and exits 0" >&2
OLD=0000000000000000000000000000000000000000
NEW=1111111111111111111111111111111111111111
REF=refs/heads/main

if printf "%s %s %s\n" "$OLD" "$NEW" "$REF" | "$hook"; then
  echo "OK: hook returned 0" >&2
else
  rc=$?
  echo "FAIL: hook exit code $rc" >&2
  exit $rc
fi

echo "[PASS] basic pre-receive behavior" >&2

