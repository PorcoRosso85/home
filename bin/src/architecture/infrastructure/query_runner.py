#!/usr/bin/env python3
"""
アーキテクチャGraph DBのクエリ実行ツール

責務:
- DQLクエリの実行
- パラメータバインディング
- 結果のフォーマット出力
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse


class QueryRunner:
    """クエリ実行クラス"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.dql_path = base_path / "dql"
    
    def load_query(self, query_path: str) -> str:
        """クエリファイルを読み込み"""
        full_path = self.dql_path / query_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"クエリファイルが見つかりません: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            # コメント行を除外してクエリを返す
            lines = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):
                    lines.append(line)
            
            return ' '.join(lines)
    
    def parse_parameters(self, param_strings: List[str]) -> Dict[str, Any]:
        """パラメータを解析"""
        params = {}
        
        for param in param_strings:
            if '=' not in param:
                continue
            
            key, value = param.split('=', 1)
            key = key.strip('-')
            
            # 型推定
            if value.lower() in ('true', 'false'):
                params[key] = value.lower() == 'true'
            elif value.isdigit():
                params[key] = int(value)
            elif value.replace('.', '').isdigit():
                params[key] = float(value)
            else:
                params[key] = value
        
        return params
    
    def format_result(self, result: List[Dict[str, Any]], format_type: str = 'table') -> str:
        """結果をフォーマット"""
        if not result:
            return "結果がありません。"
        
        if format_type == 'json':
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif format_type == 'table':
            # テーブル形式で出力
            if not result:
                return "結果がありません。"
            
            # カラム名を取得
            columns = list(result[0].keys())
            
            # カラム幅を計算
            widths = {}
            for col in columns:
                max_width = len(col)
                for row in result:
                    value_width = len(str(row.get(col, '')))
                    if value_width > max_width:
                        max_width = value_width
                widths[col] = min(max_width, 50)  # 最大幅50文字
            
            # ヘッダー行
            header = '|'
            separator = '|'
            for col in columns:
                header += f" {col:<{widths[col]}} |"
                separator += f" {'-' * widths[col]} |"
            
            lines = [header, separator]
            
            # データ行
            for row in result:
                line = '|'
                for col in columns:
                    value = str(row.get(col, ''))
                    if len(value) > widths[col]:
                        value = value[:widths[col]-3] + '...'
                    line += f" {value:<{widths[col]}} |"
                lines.append(line)
            
            return '\n'.join(lines)
        
        else:
            # 簡易形式
            lines = []
            for i, row in enumerate(result):
                lines.append(f"=== Result {i+1} ===")
                for key, value in row.items():
                    lines.append(f"{key}: {value}")
                lines.append("")
            
            return '\n'.join(lines)
    
    def execute(self, query_path: str, params: Dict[str, Any], format_type: str = 'table') -> None:
        """クエリを実行"""
        try:
            # クエリを読み込み
            query = self.load_query(query_path)
            
            print(f"実行クエリ: {query_path}")
            print(f"パラメータ: {params}")
            print("-" * 80)
            
            # 注意: 実際のKuzuDB実行はここで行う
            # 現在は移行可能性の検証のため、ダミー結果を返す
            
            # ダミー結果（実際の実装では削除）
            dummy_results = [
                {
                    "requirement_id": "req_001",
                    "requirement_title": "ユーザー認証機能",
                    "max_dependency_depth": 3,
                    "total_dependencies": 5
                },
                {
                    "requirement_id": "req_002", 
                    "requirement_title": "データベース接続",
                    "max_dependency_depth": 1,
                    "total_dependencies": 2
                }
            ]
            
            # 結果をフォーマットして出力
            formatted_result = self.format_result(dummy_results, format_type)
            print(formatted_result)
            
        except Exception as e:
            print(f"エラー: {str(e)}", file=sys.stderr)
            sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='アーキテクチャGraph DBクエリ実行ツール')
    parser.add_argument('command', choices=['execute'], help='実行コマンド')
    parser.add_argument('query', help='クエリファイルパス (例: analysis/analyze_dependencies_depth.cypher)')
    parser.add_argument('--format', choices=['table', 'json', 'simple'], default='table', help='出力形式')
    parser.add_argument('params', nargs='*', help='クエリパラメータ (例: --id=req_001)')
    
    args = parser.parse_args()
    
    # スクリプトの場所から基底パスを特定
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent
    
    runner = QueryRunner(base_path)
    
    if args.command == 'execute':
        # パラメータを解析
        params = runner.parse_parameters(args.params)
        
        # クエリを実行
        runner.execute(args.query, params, args.format)


if __name__ == "__main__":
    main()