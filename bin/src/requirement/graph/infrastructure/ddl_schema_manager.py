"""DDLスキーマ管理モジュール"""

import os
import re
from typing import List, Tuple, Optional
from datetime import datetime


class DDLSchemaManager:
    """DDLスキーマの適用とロールバックを管理"""
    
    def __init__(self, connection):
        self.conn = connection
        self.applied_statements = []
        
    def apply_schema(self, schema_path: str) -> Tuple[bool, List[str]]:
        """
        スキーマファイルを適用
        
        Returns:
            (成功フラグ, 適用されたステートメントのリスト)
        """
        if not os.path.exists(schema_path):
            return False, [f"Schema file not found: {schema_path}"]
            
        with open(schema_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # コメントと空行を除去
        statements = self._parse_cypher_statements(content)
        
        # 重複するREL TABLEを処理
        statements = self._handle_duplicate_rel_tables(statements)
        
        results = []
        for stmt in statements:
            # CREATE INDEXはKuzuDBでサポートされていないためスキップ
            if re.search(r'CREATE\s+INDEX', stmt, re.IGNORECASE):
                results.append(f"⚠ Skipped (unsupported): {stmt[:50]}...")
                continue
                
            try:
                self.conn.execute(stmt)
                self.applied_statements.append(stmt)
                results.append(f"✓ Applied: {stmt[:50]}...")
            except Exception as e:
                results.append(f"✗ Failed: {stmt[:50]}... - {str(e)}")
                return False, results
                
        return True, results
    
    def _parse_cypher_statements(self, content: str) -> List[str]:
        """Cypherステートメントをパース"""
        # ブロックコメントを先に除去
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # 行ごとに処理
        lines = []
        in_string = False
        for line in content.split('\n'):
            # 文字列リテラル内でない場合のみコメントを除去
            processed_line = ""
            i = 0
            while i < len(line):
                if line[i] == "'" and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                    processed_line += line[i]
                elif not in_string and i < len(line) - 1 and line[i:i+2] == '--':
                    # SQLスタイルのコメント
                    break
                elif not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                    # C++スタイルのコメント
                    break
                else:
                    processed_line += line[i]
                i += 1
            
            processed_line = processed_line.strip()
            if processed_line:
                lines.append(processed_line)
        
        # ステートメントを分割（セミコロンで区切る）
        full_text = ' '.join(lines)
        
        # ステートメントを抽出
        statements = []
        for part in full_text.split(';'):
            part = part.strip()
            if part:
                statements.append(part + ';')
                
        return statements
    
    def _handle_duplicate_rel_tables(self, statements: List[str]) -> List[str]:
        """重複するREL TABLEを処理"""
        processed = []
        rel_table_names = {}
        
        for stmt in statements:
            # REL TABLEの場合
            match = re.search(r'CREATE\s+REL\s+TABLE\s+(\w+)\s*\((.*?)\)', stmt, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1)
                table_def = match.group(2).strip()
                
                # FROM/TO情報を抽出
                from_to_match = re.search(r'FROM\s+(\w+)\s+TO\s+(\w+)', table_def, re.IGNORECASE)
                if from_to_match:
                    from_node = from_to_match.group(1)
                    to_node = from_to_match.group(2)
                    
                    # 同じ名前のREL TABLEが既に存在する場合
                    if table_name in rel_table_names:
                        # サフィックスを追加して一意な名前にする
                        suffix = f"_{from_node}_{to_node}"
                        new_table_name = f"{table_name}{suffix}"
                        new_stmt = stmt.replace(f"CREATE REL TABLE {table_name}", f"CREATE REL TABLE {new_table_name}")
                        processed.append(new_stmt)
                    else:
                        rel_table_names[table_name] = True
                        processed.append(stmt)
                else:
                    processed.append(stmt)
            else:
                processed.append(stmt)
        
        return processed
    
    def rollback(self) -> Tuple[bool, List[str]]:
        """適用したスキーマをロールバック"""
        results = []
        
        # 逆順でDROPを実行
        for stmt in reversed(self.applied_statements):
            try:
                drop_stmt = self._generate_drop_statement(stmt)
                if drop_stmt:
                    self.conn.execute(drop_stmt)
                    results.append(f"✓ Dropped: {drop_stmt}")
            except Exception as e:
                results.append(f"✗ Failed to drop: {str(e)}")
                
        self.applied_statements.clear()
        return True, results
    
    def _generate_drop_statement(self, create_stmt: str) -> Optional[str]:
        """CREATEステートメントから対応するDROPステートメントを生成"""
        # NODE TABLE
        match = re.search(r'CREATE\s+NODE\s+TABLE\s+(\w+)', create_stmt, re.IGNORECASE)
        if match:
            return f"DROP TABLE {match.group(1)};"
            
        # REL TABLE
        match = re.search(r'CREATE\s+REL\s+TABLE\s+(\w+)', create_stmt, re.IGNORECASE)
        if match:
            return f"DROP TABLE {match.group(1)};"
            
        # INDEX
        match = re.search(r'CREATE\s+INDEX\s+(\w+)', create_stmt, re.IGNORECASE)
        if match:
            return f"DROP INDEX {match.group(1)};"
            
        return None
    
    def create_test_data(self) -> Tuple[bool, List[str]]:
        """テストデータを作成"""
        test_statements = [
            # LocationURI
            "CREATE (l1:LocationURI {id: 'req://L0/vision/req_001'});",
            "CREATE (l2:LocationURI {id: 'req://L0/vision/auth/req_002'});",
            "CREATE (l3:LocationURI {id: 'file://src/auth/login.py'});",
            
            # RequirementEntity
            "CREATE (r1:RequirementEntity {id: 'req_001', title: 'ビジョン定義', description: 'システム全体のビジョン', priority: 'high', requirement_type: 'functional', verification_required: true});",
            "CREATE (r2:RequirementEntity {id: 'req_002', title: 'ユーザー認証', description: 'OAuth2による認証実装', priority: 'high', requirement_type: 'functional', verification_required: true});",
            
            # CodeEntity
            "CREATE (c1:CodeEntity {persistent_id: 'func_login_001', name: 'login', type: 'function', signature: 'login(username, password)', complexity: 15, start_position: 10, end_position: 50});",
            
            # 関係（リネームされたテーブル名を使用）
            "MATCH (l:LocationURI {id: 'req://L0/vision/req_001'}), (r:RequirementEntity {id: 'req_001'}) CREATE (l)-[:LOCATES_LocationURI_RequirementEntity {entity_type: 'requirement'}]->(r);",
            "MATCH (l:LocationURI {id: 'req://L0/vision/auth/req_002'}), (r:RequirementEntity {id: 'req_002'}) CREATE (l)-[:LOCATES_LocationURI_RequirementEntity {entity_type: 'requirement'}]->(r);",
            "MATCH (l:LocationURI {id: 'file://src/auth/login.py'}), (c:CodeEntity {persistent_id: 'func_login_001'}) CREATE (l)-[:LOCATES {entity_type: 'code'}]->(c);",
            "MATCH (r:RequirementEntity {id: 'req_002'}), (c:CodeEntity {persistent_id: 'func_login_001'}) CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(c);",
        ]
        
        results = []
        for stmt in test_statements:
            try:
                self.conn.execute(stmt)
                results.append(f"✓ Created: {stmt[:50]}...")
            except Exception as e:
                results.append(f"✗ Failed: {stmt[:50]}... - {str(e)}")
                # エラーがあっても続行
                
        return len([r for r in results if "✗" in r]) == 0, results
