
'print文を構造化ログに置換するヘルパー関数\n\nASTを使用してPythonコード内のprint文を安全にlogger呼び出しに変換する\n'
import ast
import sys
from typing import Optional, List, Union, Any
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class PrintReplacerTransformer(ast.NodeTransformer):
    'print文をlogger呼び出しに変換するASTトランスフォーマー'

    def __init__(self, logger_name: str='logger', stderr_level: str='error'):
        self.logger_name = logger_name
        self.stderr_level = stderr_level
        self.has_logging_import = False
        self.has_logger_definition = False

    def visit_Import(self, node: ast.Import) -> ast.Import:
        'import文をチェックしてlogging importの存在を確認'
        for alias in node.names:
            if (alias.name == 'logging'):
                self.has_logging_import = True
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        'from import文をチェック'
        if (node.module == 'logging'):
            self.has_logging_import = True
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        '代入文をチェックしてlogger定義の存在を確認'
        if ((len(node.targets) == 1) and isinstance(node.targets[0], ast.Name) and (node.targets[0].id == self.logger_name)):
            if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name) and (node.value.func.value.id == 'logging') and (node.value.func.attr == 'getLogger')):
                self.has_logger_definition = True
        return node

    def visit_Call(self, node: ast.Call) -> Union[(ast.Call, ast.Expr)]:
        'print呼び出しをlogger呼び出しに変換'
        self.generic_visit(node)
        if (not (isinstance(node.func, ast.Name) and (node.func.id == 'print'))):
            return node
        args = node.args
        keywords = {kw.arg: kw.value for kw in node.keywords}
        log_level = 'info'
        if ('file' in keywords):
            file_arg = keywords['file']
            if (isinstance(file_arg, ast.Attribute) and isinstance(file_arg.value, ast.Name) and (file_arg.value.id == 'sys') and (file_arg.attr == 'stderr')):
                log_level = self.stderr_level
        logger_call = ast.Call(func=ast.Attribute(value=ast.Name(id=self.logger_name, ctx=ast.Load()), attr=log_level, ctx=ast.Load()), args=self._convert_print_args(args), keywords=[])
        return logger_call

    def _convert_print_args(self, args: List[ast.expr]) -> List[ast.expr]:
        'print文の引数をlogger用の引数に変換'
        if (not args):
            return [ast.Constant(value='')]
        if (len(args) == 1):
            arg = args[0]
            if isinstance(arg, ast.JoinedStr):
                return [arg]
            else:
                return [arg]
        format_parts = []
        format_args = []
        for arg in args:
            if (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
                format_parts.append(arg.value)
            else:
                format_parts.append('%s')
                format_args.append(arg)
        format_string = ' '.join(format_parts)
        result_args = [ast.Constant(value=format_string)]
        result_args.extend(format_args)
        return result_args

class PrintReplacer():
    'print文を構造化ログに置換するメインクラス'

    def __init__(self, logger_name: str='logger', stderr_level: str='error'):
        '\n        Args:\n            logger_name: 生成するlogger変数の名前\n            stderr_level: sys.stderrへのprintを置換するログレベル\n        '
        self.logger_name = logger_name
        self.stderr_level = stderr_level

    def replace_prints(self, source_code: str) -> str:
        '\n        ソースコード内のprint文をlogger呼び出しに置換\n        \n        Args:\n            source_code: 置換対象のPythonソースコード\n            \n        Returns:\n            置換済みのソースコード\n            \n        Raises:\n            SyntaxError: 構文エラーのあるコードが渡された場合\n        '
        try:
            tree = ast.parse(source_code)
            transformer = PrintReplacerTransformer(logger_name=self.logger_name, stderr_level=self.stderr_level)
            transformed_tree = transformer.visit(tree)
            self._add_logging_imports(transformed_tree, transformer)
            try:
                return ast.unparse(transformed_tree)
            except AttributeError:
                try:
                    import astunparse
                    return astunparse.unparse(transformed_tree)
                except ImportError:
                    raise RuntimeError('ast.unparse is not available and astunparse is not installed. Please use Python 3.9+ or install astunparse package.')
        except SyntaxError as e:
            raise SyntaxError(f'Invalid Python syntax: {e}')

    def _add_logging_imports(self, tree: ast.AST, transformer: PrintReplacerTransformer):
        '必要なloggingのimportとlogger定義を追加'
        if (not hasattr(tree, 'body')):
            return
        additions = []
        if (not transformer.has_logging_import):
            logging_import = ast.Import(names=[ast.alias(name='logging', asname=None)])
            additions.append(logging_import)
        if (not transformer.has_logger_definition):
            logger_assign = ast.Assign(targets=[ast.Name(id=self.logger_name, ctx=ast.Store())], value=ast.Call(func=ast.Attribute(value=ast.Name(id='logging', ctx=ast.Load()), attr='getLogger', ctx=ast.Load()), args=[ast.Name(id='__name__', ctx=ast.Load())], keywords=[]))
            additions.append(logger_assign)
        if additions:
            insert_pos = 0
            for (i, node) in enumerate(tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_pos = (i + 1)
                elif (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)):
                    if ((i == 0) or ((i == 1) and isinstance(tree.body[0], (ast.Import, ast.ImportFrom)))):
                        insert_pos = (i + 1)
                else:
                    break
            for addition in reversed(additions):
                tree.body.insert(insert_pos, addition)

    def process_file(self, file_path: Union[(str, Path)], output_path: Optional[Union[(str, Path)]]=None, backup: bool=True) -> bool:
        '\n        ファイルのprint文を置換して保存\n        \n        Args:\n            file_path: 処理対象のファイルパス\n            output_path: 出力先パス（Noneの場合は元ファイルを上書き）\n            backup: 元ファイルのバックアップを作成するか\n            \n        Returns:\n            処理が成功したかどうか\n        '
        file_path = Path(file_path)
        if (not file_path.exists()):
            raise FileNotFoundError(f'File not found: {file_path}')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            replaced_code = self.replace_prints(source_code)
            if (output_path is None):
                output_path = file_path
            else:
                output_path = Path(output_path)
            if (backup and (output_path == file_path)):
                backup_path = file_path.with_suffix((file_path.suffix + '.bak'))
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(source_code)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(replaced_code)
            return True
        except Exception as e:
            logger.error(f'Error processing file {file_path}: {e}')
            return False

    def process_directory(self, directory_path: Union[(str, Path)], pattern: str='*.py', recursive: bool=True, backup: bool=True) -> List[Path]:
        '\n        ディレクトリ内のPythonファイルを一括処理\n        \n        Args:\n            directory_path: 処理対象のディレクトリパス\n            pattern: ファイルパターン\n            recursive: 再帰的に処理するか\n            backup: バックアップを作成するか\n            \n        Returns:\n            処理に成功したファイルのリスト\n        '
        directory_path = Path(directory_path)
        if ((not directory_path.exists()) or (not directory_path.is_dir())):
            raise ValueError(f'Invalid directory path: {directory_path}')
        if recursive:
            files = list(directory_path.rglob(pattern))
        else:
            files = list(directory_path.glob(pattern))
        successful_files = []
        for file_path in files:
            try:
                if self.process_file(file_path, backup=backup):
                    successful_files.append(file_path)
            except Exception as e:
                logger.error(f'Failed to process {file_path}: {e}')
        return successful_files

def main():
    'CLI エントリーポイント'
    import argparse
    parser = argparse.ArgumentParser(description='Replace print statements with structured logging')
    parser.add_argument('target', help='File or directory to process')
    parser.add_argument('--logger-name', default='logger', help='Name of the logger variable (default: logger)')
    parser.add_argument('--stderr-level', default='error', help='Log level for stderr prints (default: error)')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup files')
    parser.add_argument('--pattern', default='*.py', help='File pattern for directory processing (default: *.py)')
    parser.add_argument('--no-recursive', action='store_true', help="Don't process directories recursively")
    args = parser.parse_args()
    replacer = PrintReplacer(logger_name=args.logger_name, stderr_level=args.stderr_level)
    target_path = Path(args.target)
    backup = (not args.no_backup)
    try:
        if target_path.is_file():
            success = replacer.process_file(target_path, backup=backup)
            if success:
                logger.info(f'Successfully processed: {target_path}')
            else:
                sys.exit(1)
        elif target_path.is_dir():
            successful_files = replacer.process_directory(target_path, pattern=args.pattern, recursive=(not args.no_recursive), backup=backup)
            logger.info(f'Successfully processed {len(successful_files)} files')
            if successful_files:
                for file_path in successful_files:
                    logger.info(f'  - {file_path}')
        else:
            logger.info(f'Error: {target_path} is not a valid file or directory')
            sys.exit(1)
    except Exception as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
if (__name__ == '__main__'):
    main()
