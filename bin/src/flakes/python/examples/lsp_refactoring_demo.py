#!/usr/bin/env python3
"""
LSPリファクタリングのデモンストレーション

このスクリプトは、絶対パスから相対パスへの変換プロセスと
pyright/ruffのLSP機能を示します。
"""

import subprocess
import json
from pathlib import Path


def run_pyright(path: str) -> dict:
    """pyrightを実行してJSON結果を取得"""
    result = subprocess.run(
        ["pyright", "--outputjson", path],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        return json.loads(result.stdout)
    return {"error": result.stderr}


def run_ruff(path: str) -> str:
    """ruffを実行して結果を取得"""
    result = subprocess.run(
        ["ruff", "check", path, "--output-format", "json"],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        return json.loads(result.stdout)
    return []


def demonstrate_refactoring():
    """リファクタリングプロセスのデモ"""
    
    print("=== LSPリファクタリングデモ ===\n")
    
    # 1. 絶対インポートの解析
    print("1. 絶対インポートの解析:")
    abs_result = run_pyright("examples/absolute_imports")
    print(f"   - エラー数: {abs_result.get('summary', {}).get('errorCount', 0)}")
    print(f"   - 警告数: {abs_result.get('summary', {}).get('warningCount', 0)}")
    
    # 2. 相対インポートの解析
    print("\n2. 相対インポートの解析:")
    rel_result = run_pyright("examples/relative_imports")
    print(f"   - エラー数: {rel_result.get('summary', {}).get('errorCount', 0)}")
    print(f"   - 警告数: {rel_result.get('summary', {}).get('warningCount', 0)}")
    
    # 3. Ruffによるスタイルチェック
    print("\n3. Ruffによるスタイルチェック:")
    ruff_abs = run_ruff("examples/absolute_imports")
    ruff_rel = run_ruff("examples/relative_imports")
    print(f"   - 絶対インポート: {len(ruff_abs)} 件の問題")
    print(f"   - 相対インポート: {len(ruff_rel)} 件の問題")
    
    # 4. LSPの利点
    print("\n4. LSPの利点:")
    print("   - リアルタイムエラー検出")
    print("   - 自動補完のサポート")
    print("   - リファクタリング支援")
    print("   - 型情報の提供")
    print("   - インポートパスの検証")


if __name__ == "__main__":
    demonstrate_refactoring()