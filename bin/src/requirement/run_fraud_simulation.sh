#!/bin/bash
# 不正検知システムシミュレーション実行スクリプト

export LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/
export RGL_DB_PATH=/home/nixos/bin/src/kuzu/kuzu_db

echo "y" | python fraud_detection_complete.py