#!/usr/bin/env bash
nix develop 2>/dev/null -c bash -c "
  wrangler tail stg-waku-init --format json 2>/dev/null &
  TAIL_PID=\$!
  sleep 3
  kill \$TAIL_PID 2>/dev/null
" | grep '^{' | head -1