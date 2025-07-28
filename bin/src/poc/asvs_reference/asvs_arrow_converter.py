"""
ASVS Arrow Converter

Markdownを解析してApache Arrow形式に変換するライブラリ
KuzuDB依存を削除し、純粋な変換機能に特化
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc

from asvs_arrow_types import (
    ASVSRequirementRow,
    ASVSMetadata,
    ASVS_ARROW_SCHEMA
)


class ASVSArrowConverter:
    """ASVS MarkdownをApache Arrow形式に変換"""
    
    def __init__(self, asvs_source_path: str):
        """
        Args:
            asvs_source_path: ASVS Markdownファイルのパス（flake inputから）
        """
        self.source_path = Path(asvs_source_path)
        self.version = self._detect_version()
    
    def _detect_version(self) -> str:
        """ディレクトリ名からバージョンを検出"""
        # /path/to/5.0 -> "5.0"
        return self.source_path.name
    
    def get_requirements_table(self) -> pa.Table:
        """MarkdownをArrow Tableに変換
        
        Returns:
            pa.Table: ASVS要件のArrow Table
        """
        requirements = self._parse_all_requirements()
        
        # データを辞書形式に整理
        data = {
            'uri': [],
            'number': [],
            'description': [],
            'level1': [],
            'level2': [],
            'level3': [],
            'section': [],
            'chapter': [],
            'tags': [],
            'cwe': [],
            'nist': []
        }
        
        for req in requirements:
            data['uri'].append(req['uri'])
            data['number'].append(req['number'])
            data['description'].append(req['description'])
            data['level1'].append(req['level1'])
            data['level2'].append(req['level2'])
            data['level3'].append(req['level3'])
            data['section'].append(req['section'])
            data['chapter'].append(req['chapter'])
            data['tags'].append(req.get('tags'))
            data['cwe'].append(req.get('cwe'))
            data['nist'].append(req.get('nist'))
        
        # Arrow Table作成
        table = pa.Table.from_pydict(data, schema=ASVS_ARROW_SCHEMA)
        
        # メタデータをArrow Tableに埋め込む
        metadata = {
            b'source': b'OWASP/ASVS',
            b'version': self.version.encode('utf-8'),
            b'total_requirements': str(len(requirements)).encode('utf-8'),
            b'schema_version': b'1.0'
        }
        table = table.replace_schema_metadata(metadata)
        
        return table
    
    def get_metadata(self) -> ASVSMetadata:
        """メタデータを取得
        
        Returns:
            ASVSMetadata: メタデータ情報
        """
        table = self.get_requirements_table()
        
        # レベルを計算
        level1_mask = pc.equal(table['level1'], True)
        level2_mask = pc.equal(table['level2'], True)
        level3_mask = pc.equal(table['level3'], True)
        
        levels = []
        if pc.any(level1_mask).as_py(): levels.append(1)
        if pc.any(level2_mask).as_py(): levels.append(2)
        if pc.any(level3_mask).as_py(): levels.append(3)
        
        return ASVSMetadata(
            source='OWASP/ASVS',
            version=self.version,
            total_requirements=table.num_rows,
            levels=levels,
            schema_version='1.0'
        )
    
    def _parse_all_requirements(self) -> List[ASVSRequirementRow]:
        """すべてのMarkdownファイルから要件を抽出"""
        requirements = []
        
        # V*.mdファイルを探す（両方のパターンをサポート）
        md_files = list(self.source_path.glob("V*.md"))
        if not md_files:
            # ASVS 5.0形式のパターンを試す
            md_files = list(self.source_path.glob("*-V[0-9]*-*.md"))
        
        for md_file in md_files:
            chapter_reqs = self._parse_markdown_file(md_file)
            requirements.extend(chapter_reqs)
        
        return requirements
    
    def _parse_markdown_file(self, md_path: Path) -> List[ASVSRequirementRow]:
        """単一のMarkdownファイルを解析"""
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        requirements = []
        
        # チャプター番号とタイトルを抽出
        chapter_match = re.search(r'^# V(\d+)\s+(.+)$', content, re.MULTILINE)
        if not chapter_match:
            return requirements
        
        chapter_num = chapter_match.group(1)
        chapter_name = chapter_match.group(2).strip()
        
        # セクションごとに処理
        sections = re.split(r'^## ', content, flags=re.MULTILINE)[1:]
        
        for section_content in sections:
            section_reqs = self._parse_section(section_content, chapter_num, chapter_name)
            requirements.extend(section_reqs)
        
        return requirements
    
    def _parse_section(self, section_content: str, chapter_num: str, chapter_name: str) -> List[ASVSRequirementRow]:
        """セクション内の要件を解析"""
        lines = section_content.strip().split('\n')
        if not lines:
            return []
        
        # セクション番号とタイトル
        section_match = re.match(r'V(\d+\.\d+)\s+(.+)', lines[0])
        if not section_match:
            return []
        
        section_num = section_match.group(1)
        section_name = section_match.group(2).strip()
        
        requirements = []
        
        # テーブルを探す
        in_table = False
        for line in lines:
            if '|' in line and '---' in line:
                in_table = True
                continue
            
            if in_table and '|' in line:
                req = self._parse_requirement_line(line, chapter_num, chapter_name, section_num, section_name)
                if req:
                    requirements.append(req)
        
        return requirements
    
    def _parse_requirement_line(self, line: str, chapter_num: str, chapter_name: str, 
                               section_num: str, section_name: str) -> Optional[ASVSRequirementRow]:
        """テーブル行から要件を抽出"""
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 4:  # ASVS 5.0 has 4 parts: |, #, Description, Level, |
            return None
        
        # 要件番号のパターン（**6.1.1** のような形式）
        number_text = parts[1].strip('*').strip()
        number_match = re.match(r'(\d+\.\d+\.\d+)', number_text)
        if not number_match:
            return None
        
        number = number_match.group(1)
        description = parts[2].strip()
        
        # レベル判定（ASVS 5.0形式）
        level_str = parts[3].strip()
        try:
            level_num = int(level_str)
            level1 = level_num >= 1
            level2 = level_num >= 2
            level3 = level_num >= 3
        except ValueError:
            # 数値でない場合は旧形式を試す
            level1 = '✓' in level_str or 'X' in level_str.upper() or '1' in level_str
            level2 = '✓' in level_str or 'X' in level_str.upper() or '2' in level_str
            level3 = '✓' in level_str or 'X' in level_str.upper() or '3' in level_str
        
        # CWE抽出
        cwe_matches = re.findall(r'CWE-(\d+)', description)
        cwe_list = [int(cwe) for cwe in cwe_matches] if cwe_matches else None
        
        return ASVSRequirementRow(
            uri=f'asvs:{self.version}:req:{number}',
            number=number,
            description=description,
            level1=level1,
            level2=level2,
            level3=level3,
            section=f'{section_num} {section_name}',
            chapter=f'{chapter_num} {chapter_name}',
            tags=None,  # 将来の拡張用
            cwe=cwe_list,
            nist=None   # 将来の拡張用
        )
    
    def to_parquet(self, output_path: str, compression: str = 'snappy') -> None:
        """Arrow TableをParquetファイルに保存
        
        Args:
            output_path: 出力ファイルパス
            compression: 圧縮形式 ('snappy', 'gzip', 'brotli', None)
        """
        table = self.get_requirements_table()
        pq.write_table(table, output_path, compression=compression)


# 使用例
if __name__ == "__main__":
    # flake inputからのパス
    converter = ASVSArrowConverter("/nix/store/.../asvs-source/5.0")
    
    # Arrow Tableを直接取得
    table = converter.get_requirements_table()
    print(f"Arrow table shape: {table.shape}")
    print(f"Schema: {table.schema}")
    
    # メタデータを取得
    metadata = converter.get_metadata()
    print(f"Version: {metadata['version']}")
    print(f"Total requirements: {metadata['total_requirements']}")
    
    # Parquetへの永続化
    converter.to_parquet("asvs_v5.parquet")
    
    # embedライブラリでの使用例
    # embed_lib.process(table, text_columns=['description'])
    
    # kuzuへのインポート例
    # conn.execute("COPY Requirement FROM table")