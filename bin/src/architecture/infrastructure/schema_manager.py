
'\nアーキテクチャGraph DBのスキーマ管理ツール\n\n責務:\n- DDL個別定義から統合スキーマを生成\n- スキーママイグレーションの適用\n- スキーマ検証\n'
import os
from pathlib import Path
from typing import List, Dict, Any
import sys
import logging
logger = logging.getLogger(__name__)

class SchemaManager():
    'スキーマ管理クラス'

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.ddl_path = (base_path / 'ddl')
        self.core_path = (self.ddl_path / 'core')
        self.migrations_path = (self.ddl_path / 'migrations')
        self.output_schema = (self.ddl_path / 'schema.cypher')

    def collect_node_definitions(self) -> List[str]:
        'ノード定義を収集'
        nodes_path = (self.core_path / 'nodes')
        definitions = []
        if nodes_path.exists():
            for file in sorted(nodes_path.glob('*.cypher')):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        definitions.append(f'''// Source: {file.name}
{content}''')
        return definitions

    def collect_edge_definitions(self) -> List[str]:
        'エッジ定義を収集'
        edges_path = (self.core_path / 'edges')
        definitions = []
        if edges_path.exists():
            for file in sorted(edges_path.glob('*.cypher')):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        definitions.append(f'''// Source: {file.name}
{content}''')
        return definitions

    def generate_integrated_schema(self) -> str:
        '統合スキーマを生成'
        schema_parts = []
        schema_parts.append('// Architecture Graph DB 統合スキーマ\n// 自動生成ファイル - 直接編集禁止\n// 生成元: ddl/core/nodes/* および ddl/core/edges/*\n\n// ========================================\n// ノードテーブル定義\n// ========================================\n')
        node_definitions = self.collect_node_definitions()
        schema_parts.extend(node_definitions)
        schema_parts.append('\n// ========================================\n// エッジテーブル定義\n// ========================================\n')
        edge_definitions = self.collect_edge_definitions()
        schema_parts.extend(edge_definitions)
        return '\n\n'.join(schema_parts)

    def write_schema(self, schema: str) -> None:
        'スキーマをファイルに書き込み'
        with open(self.output_schema, 'w', encoding='utf-8') as f:
            f.write(schema)
        logger.info(f'統合スキーマを生成しました: {self.output_schema}')

    def validate_schema(self, schema: str) -> bool:
        'スキーマの妥当性を検証'
        required_tables = ['RequirementEntity', 'LocationURI', 'VersionState', 'LOCATES', 'TRACKS_STATE_OF', 'DEPENDS_ON']
        for table in required_tables:
            if (table not in schema):
                logger.info(f"エラー: 必須テーブル '{table}' が見つかりません")
                return False
        return True

    def apply(self) -> None:
        'スキーマを適用'
        schema = self.generate_integrated_schema()
        if (not self.validate_schema(schema)):
            logger.info('スキーマ検証に失敗しました')
            sys.exit(1)
        self.write_schema(schema)
        logger.info('\nスキーマ適用の準備が完了しました。')
        logger.info('KuzuDBへの適用は以下のコマンドで実行してください:')
        logger.info(f'  kuzu apply {self.output_schema}')

def main():
    'メイン関数'
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent
    if (len(sys.argv) < 2):
        logger.info('使用方法: python schema_manager.py <command>')
        logger.info('コマンド:')
        logger.info('  apply    - 統合スキーマを生成')
        sys.exit(1)
    command = sys.argv[1]
    manager = SchemaManager(base_path)
    if (command == 'apply'):
        manager.apply()
    else:
        logger.info(f'不明なコマンド: {command}')
        sys.exit(1)
if (__name__ == '__main__'):
    main()
