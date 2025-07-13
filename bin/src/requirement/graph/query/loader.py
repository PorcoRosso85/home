"""
クエリローダー - Cypherクエリファイルの安全な読み込み

規約準拠:
- security.md: パラメータ化クエリによるSQLインジェクション防止
- module_design.md: 1ファイル1機能、純粋関数優先
- layered_architecture.md: インフラストラクチャ層のデータアクセス
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path


class QueryLoader:
    """Cypherクエリファイルの安全な読み込みと実行"""
    
    def __init__(self, query_dir: Optional[str] = None):
        """
        Args:
            query_dir: クエリディレクトリのパス（Noneの場合は自動検出）
        """
        if query_dir is None:
            # queryディレクトリを自動検出
            current_dir = Path(__file__).parent
            self.query_dir = current_dir
        else:
            self.query_dir = Path(query_dir)
        
        self.dml_dir = self.query_dir / "dml"
        self.dql_dir = self.query_dir / "dql"
    
    def load_query(self, query_name: str, query_type: str = "auto") -> str:
        """
        クエリファイルを読み込み
        
        Args:
            query_name: クエリ名（拡張子なし）
            query_type: "dml", "dql", "auto"（自動判定）
            
        Returns:
            Cypherクエリ文字列
            
        Raises:
            FileNotFoundError: クエリファイルが見つからない
        """
        if query_type == "auto":
            # DMLとDQLの両方を検索
            for dir_path, type_name in [(self.dml_dir, "dml"), (self.dql_dir, "dql")]:
                query_path = dir_path / f"{query_name}.cypher"
                if query_path.exists():
                    return self._read_query_file(query_path)
            
            raise FileNotFoundError(f"Query '{query_name}' not found in dml or dql directories")
        
        elif query_type == "dml":
            query_path = self.dml_dir / f"{query_name}.cypher"
        elif query_type == "dql":
            query_path = self.dql_dir / f"{query_name}.cypher"
        else:
            raise ValueError(f"Invalid query_type: {query_type}. Use 'dml', 'dql', or 'auto'")
        
        if not query_path.exists():
            raise FileNotFoundError(f"Query file not found: {query_path}")
        
        return self._read_query_file(query_path)
    
    def _read_query_file(self, query_path: Path) -> str:
        """
        クエリファイルを安全に読み込み
        
        Args:
            query_path: クエリファイルのパス
            
        Returns:
            クエリ文字列（コメント除去、正規化済み）
        """
        try:
            with open(query_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # コメント行を除去（//で始まる行）
            lines = content.split('\n')
            query_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('//'):
                    query_lines.append(line)
            
            query = '\n'.join(query_lines).strip()
            
            if not query:
                raise ValueError(f"Empty query file: {query_path}")
            
            return query
            
        except Exception as e:
            raise RuntimeError(f"Failed to read query file {query_path}: {e}")
    
    def execute_query(self, repository: Dict[str, Any], query_name: str, 
                     params: Dict[str, Any], query_type: str = "auto") -> Dict[str, Any]:
        """
        クエリを読み込んで実行（推奨インターフェース）
        
        Args:
            repository: KuzuDBリポジトリ
            query_name: クエリ名
            params: クエリパラメータ
            query_type: クエリタイプ
            
        Returns:
            実行結果
        """
        query = self.load_query(query_name, query_type)
        return repository["execute"](query, params)


# インスタンス生成用のファクトリ関数（conventions準拠）
def create_query_loader(query_dir: Optional[str] = None) -> QueryLoader:
    """QueryLoaderのファクトリ関数"""
    return QueryLoader(query_dir)


# モジュールレベルのデフォルトローダー
_default_loader = None

def get_default_loader() -> QueryLoader:
    """デフォルトのQueryLoaderインスタンスを取得"""
    global _default_loader
    if _default_loader is None:
        _default_loader = QueryLoader()
    return _default_loader


def load_query(query_name: str, query_type: str = "auto") -> str:
    """便利関数: デフォルトローダーでクエリを読み込み"""
    return get_default_loader().load_query(query_name, query_type)


def execute_query(repository: Dict[str, Any], query_name: str, 
                 params: Dict[str, Any], query_type: str = "auto") -> Dict[str, Any]:
    """便利関数: デフォルトローダーでクエリを実行"""
    return get_default_loader().execute_query(repository, query_name, params, query_type)