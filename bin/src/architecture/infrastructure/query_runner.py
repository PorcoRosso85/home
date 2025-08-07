
'\nアーキテクチャGraph DBのクエリ実行ツール\n\n責務:\n- DQLクエリの実行\n- パラメータバインディング\n- 結果のフォーマット出力\n'
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import argparse
import logging
logger = logging.getLogger(__name__)
sys.path.append(str(((Path(__file__).resolve().parent.parent.parent / 'persistence') / 'kuzu_py')))
from query_loader import load_typed_query, execute_query
from errors import FileOperationError, ValidationError, NotFoundError

class QueryRunner():
    'クエリ実行クラス'

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.dql_path = (base_path / 'dql')

    def load_query(self, query_path: str) -> Union[(str, Dict[(str, Any)])]:
        'クエリファイルを読み込み（kuzu_pyのload_typed_queryを使用）'
        query_name = Path(query_path).stem
        result = load_typed_query(query_name=query_name, query_type='dql', base_dir=str(self.base_path))
        if isinstance(result, (FileOperationError, ValidationError, NotFoundError)):
            error_dict = (result.dict() if hasattr(result, 'dict') else result)
            raise FileNotFoundError(f"クエリファイルの読み込みエラー: {error_dict.get('message', str(result))}")
        return result

    def parse_parameters(self, param_strings: List[str]) -> Dict[(str, Any)]:
        'パラメータを解析'
        from infrastructure.utils.param_parser import parse_parameters
        return parse_parameters(param_strings)

    def _convert_result_to_dicts(self, result) -> List[Dict[(str, Any)]]:
        'KuzuDB結果を辞書のリストに変換（QueryExecutorの機能を統合）\n        \n        Args:\n            result: KuzuDB query result object\n            \n        Returns:\n            List of result rows as dictionaries\n        '
        columns = result.get_column_names()
        rows = []
        while result.has_next():
            row_data = result.get_next()
            row_dict = {}
            for (i, col_name) in enumerate(columns):
                row_dict[col_name] = row_data[i]
            rows.append(row_dict)
        return rows

    def execute_query_from_file(self, query_path: Path, params: Dict[(str, Any)]=None) -> List[Dict[(str, Any)]]:
        'ファイルからクエリを読み込んで実行（QueryExecutorの機能を統合）\n        \n        Args:\n            query_path: Path to file containing Cypher query\n            params: Query parameters (optional)\n            \n        Returns:\n            List of result rows as dictionaries\n        '
        with open(query_path, 'r') as f:
            query_content = f.read()
        lines = []
        for line in query_content.split('\n'):
            line = line.strip()
            if (line and (not line.startswith('--'))):
                lines.append(line)
        query = ' '.join(lines)
        return self.execute_raw_query(query, (params or {}))

    def execute_raw_query(self, query: str, params: Dict[(str, Any)]=None) -> List[Dict[(str, Any)]]:
        '生のクエリを実行（QueryExecutorの機能を統合）\n        \n        Args:\n            query: Cypher query to execute\n            params: Query parameters (optional)\n            \n        Returns:\n            List of result rows as dictionaries\n        '
        import kuzu
        db_path = ((self.base_path / 'data') / 'kuzu.db')
        db = kuzu.Database(str(db_path))
        conn = kuzu.Connection(db)
        result = conn.execute(query, (params or {}))
        return self._convert_result_to_dicts(result)

    def format_result(self, result: List[Dict[(str, Any)]], format_type: str='table') -> str:
        '結果をフォーマット'
        if (not result):
            return '結果がありません。'
        if (format_type == 'json'):
            return json.dumps(result, indent=2, ensure_ascii=False)
        elif (format_type == 'table'):
            if (not result):
                return '結果がありません。'
            columns = list(result[0].keys())
            widths = {}
            for col in columns:
                max_width = len(col)
                for row in result:
                    value_width = len(str(row.get(col, '')))
                    if (value_width > max_width):
                        max_width = value_width
                widths[col] = min(max_width, 50)
            header = '|'
            separator = '|'
            for col in columns:
                header += f' {col:<{widths[col]}} |'
                separator += f" {('-' * widths[col])} |"
            lines = [header, separator]
            for row in result:
                line = '|'
                for col in columns:
                    value = str(row.get(col, ''))
                    if (len(value) > widths[col]):
                        value = (value[:(widths[col] - 3)] + '...')
                    line += f' {value:<{widths[col]}} |'
                lines.append(line)
            return '\n'.join(lines)
        else:
            lines = []
            for (i, row) in enumerate(result):
                lines.append(f'=== Result {(i + 1)} ===')
                for (key, value) in row.items():
                    lines.append(f'{key}: {value}')
                lines.append('')
            return '\n'.join(lines)

    def execute(self, query_path: str, params: Dict[(str, Any)], format_type: str='table') -> None:
        'クエリを実行'
        try:
            query = self.load_query(query_path)
            logger.info(f'実行クエリ: {query_path}')
            logger.info(f'パラメータ: {params}')
            logger.info(('-' * 80))
            results = self.execute_raw_query(query, params)
            formatted_result = self.format_result(results, format_type)
            logger.info(formatted_result)
        except Exception as e:
            logger.error(f'エラー: {str(e)}')
            sys.exit(1)

def main():
    'メイン関数'
    parser = argparse.ArgumentParser(description='アーキテクチャGraph DBクエリ実行ツール')
    parser.add_argument('command', choices=['execute'], help='実行コマンド')
    parser.add_argument('query', help='クエリファイルパス (例: analysis/analyze_dependencies_depth.cypher)')
    parser.add_argument('--format', choices=['table', 'json', 'simple'], default='table', help='出力形式')
    parser.add_argument('params', nargs='*', help='クエリパラメータ (例: --id=req_001)')
    args = parser.parse_args()
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent
    runner = QueryRunner(base_path)
    if (args.command == 'execute'):
        params = runner.parse_parameters(args.params)
        runner.execute(args.query, params, args.format)
if (__name__ == '__main__'):
    main()
