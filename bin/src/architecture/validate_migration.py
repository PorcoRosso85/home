#!/usr/bin/env python3
"""
001_unify_naming.cypherのdry run検証スクリプト
"""

import re
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationValidator:
    """マイグレーションの構文と実行可能性を検証"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.steps: List[Dict[str, Any]] = []
        
    def parse_migration(self, content: str) -> None:
        """マイグレーションファイルを解析"""
        # コメントを除去してステートメントを抽出
        lines = content.split('\n')
        current_statement = []
        step_number = 0
        
        for line in lines:
            # コメント行をスキップ
            if line.strip().startswith('--'):
                if 'Step' in line:
                    step_match = re.search(r'Step (\d+):', line)
                    if step_match:
                        step_number = int(step_match.group(1))
                continue
                
            # 空行をスキップ
            if not line.strip():
                continue
                
            current_statement.append(line)
            
            # ステートメントの終端を検出
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                self.steps.append({
                    'step': step_number,
                    'statement': statement,
                    'type': self._get_statement_type(statement)
                })
                current_statement = []
    
    def _get_statement_type(self, statement: str) -> str:
        """ステートメントのタイプを判定"""
        statement_upper = statement.upper()
        if statement_upper.startswith('CREATE NODE TABLE'):
            return 'CREATE_NODE_TABLE'
        elif statement_upper.startswith('CREATE REL TABLE'):
            return 'CREATE_REL_TABLE'
        elif statement_upper.startswith('MATCH') and 'CREATE' in statement_upper:
            return 'COPY_DATA'
        elif statement_upper.startswith('MATCH') and 'DELETE' in statement_upper:
            return 'DELETE_RELATIONSHIP'
        elif statement_upper.startswith('DROP TABLE'):
            return 'DROP_TABLE'
        else:
            return 'UNKNOWN'
    
    def validate_syntax(self) -> None:
        """各ステートメントの構文を検証"""
        for step_info in self.steps:
            statement = step_info['statement']
            stmt_type = step_info['type']
            
            if stmt_type == 'CREATE_NODE_TABLE':
                self._validate_create_node_table(statement)
            elif stmt_type == 'COPY_DATA':
                self._validate_copy_data(statement)
            elif stmt_type == 'DELETE_RELATIONSHIP':
                self._validate_delete_relationship(statement)
            elif stmt_type == 'DROP_TABLE':
                self._validate_drop_table(statement)
    
    def _validate_create_node_table(self, statement: str) -> None:
        """CREATE NODE TABLEの構文検証"""
        if 'LocationURI' not in statement:
            self.errors.append("CREATE NODE TABLE: LocationURIテーブルが定義されていません")
        if 'PRIMARY KEY' not in statement:
            self.errors.append("CREATE NODE TABLE: PRIMARY KEYが定義されていません")
    
    def _validate_copy_data(self, statement: str) -> None:
        """データコピーの構文検証"""
        # 必要な要素をチェック
        required_elements = ['MATCH', 'CREATE', 'ImplementationURI', 'LocationURI']
        for element in required_elements:
            if element not in statement:
                self.errors.append(f"COPY_DATA: {element}が見つかりません")
        
        # プロパティコピーの確認
        if '{id: uri.id}' not in statement and '{id: parent.id}' not in statement and '{id: child.id}' not in statement:
            self.warnings.append("COPY_DATA: プロパティコピーが正しく設定されているか確認してください")
    
    def _validate_delete_relationship(self, statement: str) -> None:
        """DELETE文の構文検証"""
        if 'DELETE r' not in statement:
            self.errors.append("DELETE: リレーションシップの削除が指定されていません")
    
    def _validate_drop_table(self, statement: str) -> None:
        """DROP TABLEの構文検証"""
        if 'CASCADE' not in statement:
            self.warnings.append("DROP TABLE: CASCADEオプションが指定されていません（依存関係がある場合エラーになる可能性があります）")
    
    def check_dependencies(self) -> None:
        """依存関係のチェック"""
        # Step 1でLocationURIが作成されているか
        has_location_uri_creation = any(
            'LocationURI' in step['statement'] and step['type'] == 'CREATE_NODE_TABLE'
            for step in self.steps
        )
        
        if not has_location_uri_creation:
            self.errors.append("依存関係: LocationURIテーブルが作成されていません")
        
        # データコピー前にテーブルが存在するか
        create_step = None
        copy_steps = []
        
        for i, step in enumerate(self.steps):
            if step['type'] == 'CREATE_NODE_TABLE' and 'LocationURI' in step['statement']:
                create_step = i
            elif step['type'] == 'COPY_DATA':
                copy_steps.append(i)
        
        if create_step is not None and copy_steps:
            for copy_step in copy_steps:
                if copy_step < create_step:
                    self.errors.append(f"依存関係: ステップ{self.steps[copy_step]['step']}でLocationURIテーブルが作成前に使用されています")
    
    def check_data_integrity(self) -> None:
        """データ整合性のチェック"""
        # 全てのリレーションシップが再作成されているか
        relationships = ['LOCATES', 'TRACKS_STATE_OF', 'CONTAINS_LOCATION', 'HAS_RESPONSIBILITY']
        
        for rel in relationships:
            # 削除があるか
            has_delete = any(
                rel in step['statement'] and step['type'] == 'DELETE_RELATIONSHIP'
                for step in self.steps
            )
            
            # 再作成があるか
            has_create = any(
                rel in step['statement'] and step['type'] == 'COPY_DATA'
                for step in self.steps
            )
            
            if has_delete and not has_create:
                self.warnings.append(f"データ整合性: {rel}リレーションシップが削除されますが、再作成されていません")
            elif has_create and not has_delete:
                self.warnings.append(f"データ整合性: {rel}リレーションシップが再作成されますが、古いものが削除されていません")
    
    def generate_report(self) -> str:
        """検証レポートを生成"""
        report = []
        report.append("=== 001_unify_naming.cypher Dry Run Report ===\n")
        
        # ステップサマリー
        report.append(f"総ステップ数: {len(self.steps)}")
        report.append("\nステップ概要:")
        
        for step_info in self.steps:
            step_num = step_info['step'] if step_info['step'] > 0 else '?'
            report.append(f"  Step {step_num}: {step_info['type']}")
        
        # エラーとワーニング
        report.append(f"\n検出されたエラー: {len(self.errors)}")
        if self.errors:
            for error in self.errors:
                report.append(f"  ❌ {error}")
        
        report.append(f"\n検出された警告: {len(self.warnings)}")
        if self.warnings:
            for warning in self.warnings:
                report.append(f"  ⚠️  {warning}")
        
        # 実行可能性判定
        report.append("\n実行可能性判定:")
        if not self.errors:
            report.append("  ✅ 構文的には実行可能です")
        else:
            report.append("  ❌ エラーを修正する必要があります")
        
        # 推奨事項
        report.append("\n推奨事項:")
        report.append("  1. 実行前にデータベースのバックアップを取得してください")
        report.append("  2. 000_initial.cypherが適用済みであることを確認してください")
        report.append("  3. ImplementationURIテーブルにデータが存在する場合、移行が必要です")
        report.append("  4. 検証クエリ（65-79行目）を実行して結果を確認してください")
        
        return '\n'.join(report)


def main():
    """メイン関数"""
    migration_file = Path("/home/nixos/bin/src/architecture/001_unify_naming.cypher")
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return
    
    # ファイルを読み込み
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 検証を実行
    validator = MigrationValidator()
    validator.parse_migration(content)
    validator.validate_syntax()
    validator.check_dependencies()
    validator.check_data_integrity()
    
    # レポートを出力
    report = validator.generate_report()
    logger.info(f"Validation report:\n{report}")


if __name__ == "__main__":
    main()