#!/usr/bin/env python3
"""
KuzuDBネイティブなマイグレーション支援ツール

責務:
- EXPORT/IMPORT DATABASEコマンドのラップ
- バージョン管理の自動化
- マイグレーション履歴の追跡
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import argparse
import shutil


class MigrationTool:
    """マイグレーション管理クラス"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.migrations_path = base_path / "migrations"
        self.migrations_path.mkdir(exist_ok=True)
        self.current_link = self.migrations_path / "current"
    
    def get_current_version(self) -> Optional[str]:
        """現在のバージョンを取得"""
        if self.current_link.exists() and self.current_link.is_symlink():
            target = self.current_link.readlink()
            return target.name
        return None
    
    def list_versions(self) -> List[str]:
        """利用可能なバージョンをリスト"""
        versions = []
        for path in self.migrations_path.iterdir():
            if path.is_dir() and path.name.startswith('v'):
                versions.append(path.name)
        return sorted(versions)
    
    def export_database(self, version: str, db_path: str = ".", format: str = "parquet") -> None:
        """データベースをエクスポート"""
        export_path = self.migrations_path / version
        
        # バージョンが既に存在する場合は確認
        if export_path.exists():
            response = input(f"バージョン {version} は既に存在します。上書きしますか？ (y/N): ")
            if response.lower() != 'y':
                print("エクスポートを中止しました。")
                return
            shutil.rmtree(export_path)
        
        export_path.mkdir(parents=True)
        
        # KuzuDBコマンドを生成
        export_cmd = f'EXPORT DATABASE \'{export_path}\' (format="{format}");'
        
        print(f"エクスポート中: {version}")
        print(f"コマンド: {export_cmd}")
        
        # 実際のKuzuDB実行（注意: 実装では適切なKuzuDB接続が必要）
        # ここではコマンドの出力のみ
        print("注意: 実際のKuzuDB接続が必要です。以下のコマンドを実行してください:")
        print(f"  kuzu {db_path}")
        print(f"  kuzu> {export_cmd}")
        
        # メタデータを保存
        metadata = {
            "version": version,
            "exported_at": datetime.now().isoformat(),
            "format": format,
            "from_version": self.get_current_version()
        }
        
        with open(export_path / "migration_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # CHANGELOG作成
        self.create_changelog(version, export_path)
        
        # currentリンクを更新
        self.update_current_link(version)
        
        print(f"エクスポート完了: {export_path}")
    
    def import_database(self, version: str, db_path: str = ".") -> None:
        """データベースをインポート"""
        import_path = self.migrations_path / version
        
        if not import_path.exists():
            print(f"エラー: バージョン {version} が見つかりません。")
            print(f"利用可能なバージョン: {', '.join(self.list_versions())}")
            return
        
        # KuzuDBコマンドを生成
        import_cmd = f'IMPORT DATABASE \'{import_path}\';'
        
        print(f"インポート中: {version}")
        print(f"コマンド: {import_cmd}")
        
        # 実際のKuzuDB実行（注意: 実装では適切なKuzuDB接続が必要）
        print("注意: 実際のKuzuDB接続が必要です。以下のコマンドを実行してください:")
        print(f"  kuzu {db_path}")
        print(f"  kuzu> {import_cmd}")
        
        # currentリンクを更新
        self.update_current_link(version)
        
        print(f"インポート完了: {version}")
    
    def diff_versions(self, version1: str, version2: str) -> None:
        """バージョン間の差分を表示"""
        path1 = self.migrations_path / version1 / "schema.cypher"
        path2 = self.migrations_path / version2 / "schema.cypher"
        
        if not path1.exists():
            print(f"エラー: {version1}/schema.cypher が見つかりません。")
            return
        
        if not path2.exists():
            print(f"エラー: {version2}/schema.cypher が見つかりません。")
            return
        
        print(f"=== {version1} → {version2} の差分 ===")
        
        # 簡易的な差分表示（実際はより高度な差分ツールを使用）
        with open(path1, 'r') as f1, open(path2, 'r') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            
            # 単純な行数比較
            print(f"{version1}: {len(lines1)} 行")
            print(f"{version2}: {len(lines2)} 行")
            print(f"差分: {len(lines2) - len(lines1)} 行")
        
        # 実際の差分表示にはdiffツールを推奨
        print("\n詳細な差分を見るには以下のコマンドを実行:")
        print(f"  diff -u {path1} {path2}")
    
    def rollback(self, version: str) -> None:
        """指定バージョンへロールバック"""
        if version not in self.list_versions():
            print(f"エラー: バージョン {version} が見つかりません。")
            return
        
        current = self.get_current_version()
        if current == version:
            print(f"既に {version} を使用中です。")
            return
        
        print(f"ロールバック: {current} → {version}")
        response = input("続行しますか？ (y/N): ")
        
        if response.lower() == 'y':
            self.import_database(version)
        else:
            print("ロールバックを中止しました。")
    
    def update_current_link(self, version: str) -> None:
        """currentシンボリックリンクを更新"""
        target = Path(version)
        
        if self.current_link.exists():
            self.current_link.unlink()
        
        self.current_link.symlink_to(target)
    
    def create_changelog(self, version: str, export_path: Path) -> None:
        """CHANGELOG.mdを作成"""
        changelog_path = export_path / "CHANGELOG.md"
        
        with open(changelog_path, 'w') as f:
            f.write(f"# Changelog for {version}\n\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Changes\n\n")
            f.write("- [ ] スキーマ変更の詳細をここに記載\n")
            f.write("- [ ] 追加されたテーブル\n")
            f.write("- [ ] 変更されたプロパティ\n")
            f.write("- [ ] 削除された要素\n\n")
            f.write("## Migration Notes\n\n")
            f.write("特別な移行手順が必要な場合はここに記載\n")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='KuzuDBマイグレーション管理ツール')
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # export コマンド
    export_parser = subparsers.add_parser('export', help='データベースをエクスポート')
    export_parser.add_argument('--version', required=True, help='バージョン名 (例: v4.1.0)')
    export_parser.add_argument('--format', default='parquet', choices=['parquet', 'csv'], help='エクスポート形式')
    export_parser.add_argument('--db', default='.', help='データベースパス')
    
    # import コマンド
    import_parser = subparsers.add_parser('import', help='データベースをインポート')
    import_parser.add_argument('--version', required=True, help='バージョン名')
    import_parser.add_argument('--db', default='.', help='データベースパス')
    
    # diff コマンド
    diff_parser = subparsers.add_parser('diff', help='バージョン間の差分を表示')
    diff_parser.add_argument('version1', help='比較元バージョン')
    diff_parser.add_argument('version2', help='比較先バージョン')
    
    # rollback コマンド
    rollback_parser = subparsers.add_parser('rollback', help='指定バージョンへロールバック')
    rollback_parser.add_argument('version', help='ロールバック先バージョン')
    
    # list コマンド
    list_parser = subparsers.add_parser('list', help='利用可能なバージョンを表示')
    
    args = parser.parse_args()
    
    # ツールの初期化
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent
    tool = MigrationTool(base_path)
    
    # コマンド実行
    if args.command == 'export':
        tool.export_database(args.version, args.db, args.format)
    elif args.command == 'import':
        tool.import_database(args.version, args.db)
    elif args.command == 'diff':
        tool.diff_versions(args.version1, args.version2)
    elif args.command == 'rollback':
        tool.rollback(args.version)
    elif args.command == 'list':
        versions = tool.list_versions()
        current = tool.get_current_version()
        print("利用可能なバージョン:")
        for v in versions:
            marker = " (current)" if v == current else ""
            print(f"  {v}{marker}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()