#!/usr/bin/env python3
"""
アーキテクチャGraph DBのスキーマ管理ツール

責務:
- DDL個別定義から統合スキーマを生成
- スキーママイグレーションの適用
- スキーマ検証
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import sys


class SchemaManager:
    """スキーマ管理クラス"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.ddl_path = base_path / "ddl"
        self.core_path = self.ddl_path / "core"
        self.migrations_path = self.ddl_path / "migrations"
        self.output_schema = self.ddl_path / "schema.cypher"
    
    def collect_node_definitions(self) -> List[str]:
        """ノード定義を収集"""
        nodes_path = self.core_path / "nodes"
        definitions = []
        
        if nodes_path.exists():
            for file in sorted(nodes_path.glob("*.cypher")):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        definitions.append(f"// Source: {file.name}\n{content}")
        
        return definitions
    
    def collect_edge_definitions(self) -> List[str]:
        """エッジ定義を収集"""
        edges_path = self.core_path / "edges"
        definitions = []
        
        if edges_path.exists():
            for file in sorted(edges_path.glob("*.cypher")):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        definitions.append(f"// Source: {file.name}\n{content}")
        
        return definitions
    
    def generate_integrated_schema(self) -> str:
        """統合スキーマを生成"""
        schema_parts = []
        
        # ヘッダー
        schema_parts.append("""// Architecture Graph DB 統合スキーマ
// 自動生成ファイル - 直接編集禁止
// 生成元: ddl/core/nodes/* および ddl/core/edges/*

// ========================================
// ノードテーブル定義
// ========================================
""")
        
        # ノード定義を追加
        node_definitions = self.collect_node_definitions()
        schema_parts.extend(node_definitions)
        
        # エッジ定義セクション
        schema_parts.append("""
// ========================================
// エッジテーブル定義
// ========================================
""")
        
        # エッジ定義を追加
        edge_definitions = self.collect_edge_definitions()
        schema_parts.extend(edge_definitions)
        
        return "\n\n".join(schema_parts)
    
    def write_schema(self, schema: str) -> None:
        """スキーマをファイルに書き込み"""
        with open(self.output_schema, 'w', encoding='utf-8') as f:
            f.write(schema)
        print(f"統合スキーマを生成しました: {self.output_schema}")
    
    def validate_schema(self, schema: str) -> bool:
        """スキーマの妥当性を検証"""
        # 基本的な検証
        required_tables = [
            "RequirementEntity",
            "LocationURI", 
            "VersionState",
            "LOCATES",
            "TRACKS_STATE_OF",
            "DEPENDS_ON"
        ]
        
        for table in required_tables:
            if table not in schema:
                print(f"エラー: 必須テーブル '{table}' が見つかりません")
                return False
        
        return True
    
    def apply(self) -> None:
        """スキーマを適用"""
        # 統合スキーマを生成
        schema = self.generate_integrated_schema()
        
        # 検証
        if not self.validate_schema(schema):
            print("スキーマ検証に失敗しました")
            sys.exit(1)
        
        # ファイルに書き込み
        self.write_schema(schema)
        
        print("\nスキーマ適用の準備が完了しました。")
        print("KuzuDBへの適用は以下のコマンドで実行してください:")
        print(f"  kuzu apply {self.output_schema}")


def main():
    """メイン関数"""
    # スクリプトの場所から基底パスを特定
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent
    
    # コマンドライン引数の処理
    if len(sys.argv) < 2:
        print("使用方法: python schema_manager.py <command>")
        print("コマンド:")
        print("  apply    - 統合スキーマを生成")
        sys.exit(1)
    
    command = sys.argv[1]
    manager = SchemaManager(base_path)
    
    if command == "apply":
        manager.apply()
    else:
        print(f"不明なコマンド: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()